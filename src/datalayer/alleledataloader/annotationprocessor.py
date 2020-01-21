# -*- coding: utf-8 -*-

from api import config


class TranscriptAnnotation(object):
    """
    Calculate extra transcript related fields that depend on dynamic configs.
    """

    def __init__(self, config):
        self.config = config

    def _get_worst_consequence(self, transcripts):
        """
        Finds the transcript with the worst consequence.
        :param transcripts: List of transcripts with data
        :return: List of transcript names with the worst consequence.
        """
        if not self.config.get("transcripts", {}).get("consequences"):
            return list()

        config_consequences = self.config["transcripts"]["consequences"]

        all_consequences = set()
        for transcript in transcripts:
            all_consequences.update(transcript["consequences"])

        worst_consequence = None
        for config_consequence in config_consequences:
            if config_consequence in all_consequences:
                worst_consequence = config_consequence
                break

        worst_consequence_transcripts = list()
        for t in transcripts:
            if worst_consequence in t.get("consequences", []):
                worst_consequence_transcripts.append(t["transcript"])

        return worst_consequence_transcripts

    def process(self, annotation, genepanel=None):
        """
        :param annotation
        :param genepanel: If provided, adds filtered_transcript to output,
                          containing the name of the transcripts found in
                          genepanel.
        :type genepanel: vardb.datamodel.gene.Genepanel
        """

        result = dict()
        if "transcripts" not in annotation:
            return result

        result["transcripts"] = annotation["transcripts"]
        result["worst_consequence"] = self._get_worst_consequence(result["transcripts"])
        return result


class AnnotationProcessor(object):
    @staticmethod
    def process(annotation, custom_annotation=None, genepanel=None):
        """
        Expands/changes/merges input annotation data inplace.

        :param annotation:
        :param custom_annotation:
        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :return: Modified annotation data
        """

        if "transcripts" in annotation:
            annotation.update(
                TranscriptAnnotation(config.config).process(annotation, genepanel=genepanel)
            )

        if custom_annotation:
            # Merge/overwrite annotation with custom_annotation
            for key in list(config.config["custom_annotation"].keys()):
                if key in custom_annotation:
                    if key not in annotation:
                        annotation[key] = dict()
                    annotation[key].update(custom_annotation[key])

            # References are merged specially
            if "references" in annotation and "references" in custom_annotation:
                for ca_ref in custom_annotation["references"]:
                    if "source_info" not in ca_ref:
                        ca_ref["source_info"] = dict()

                    # A reference can come from several sources, if so only merge the source
                    assert ca_ref.get("id") or ca_ref.get("pubmed_id"), ca_ref
                    existing_ref = None
                    for r in annotation["references"]:
                        for id in ["id", "pubmed_id"]:
                            if r.get(id) is not None and r.get(id) == ca_ref.get(id):
                                existing_ref = r
                                break

                    if existing_ref is not None:
                        existing_ref["sources"] = existing_ref["sources"] + ca_ref["sources"]
                        continue

                    annotation["references"].append(ca_ref)

        # DEPRECATION: Rename inDB AF to OUSWES on the fly.
        # Can be removed once database is remade in production.
        if "frequencies" in annotation and "inDB" in annotation["frequencies"]:
            for item in ["freq", "count"]:
                if item in annotation["frequencies"]["inDB"]:
                    if "AF" in annotation["frequencies"]["inDB"][item]:
                        annotation["frequencies"]["inDB"][item]["OUSWES"] = annotation[
                            "frequencies"
                        ]["inDB"][item]["AF"]
                        del annotation["frequencies"]["inDB"][item]["AF"]
            if (
                "indications" in annotation["frequencies"]["inDB"]
                and "OUSWES" not in annotation["frequencies"]["inDB"]["indications"]
            ):
                annotation["frequencies"]["inDB"]["indications"] = {
                    "OUSWES": annotation["frequencies"]["inDB"]["indications"]
                }
        # END DEPRECATION

        return annotation
