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
            annotation["external"] = {
                **annotation.get("external", {}),
                **custom_annotation.get("external", {}),
            }
            annotation["prediction"] = {
                **annotation.get("prediction", {}),
                **custom_annotation.get("prediction", {}),
            }
            # References are merged specially
            annotation["references"] = annotation.get("references", []) + custom_annotation.get(
                "references", []
            )

        return annotation
