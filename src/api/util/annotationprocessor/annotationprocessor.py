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
        if not self.config.get('transcripts', {}).get('consequences'):
            return list()

        # Get minimum index for each item (since each have several consequences), then sort by that index
        consequences = self.config['transcripts']['consequences']

        def sort_func(x):
            if 'consequences' in x and x['consequences']:
                return min(consequences.index(c) for c in x['consequences'])
            else:
                return 9999999
        sorted_transcripts = sorted(transcripts, key=sort_func)

        worst_consequences = list()
        if sorted_transcripts:
            worst_consequence = sorted_transcripts[0]['consequences']
            for t in sorted_transcripts:
                if any(c in t.get('consequences', []) for c in worst_consequence):
                    worst_consequences.append(t['transcript'])
                else:
                    break

            return worst_consequences

    def process(self, annotation, genepanel=None):
        """
        :param annotation
        :param genepanel: If provided, adds filtered_transcript to output,
                          containing the name of the transcripts found in
                          genepanel.
        :type genepanel: vardb.datamodel.gene.Genepanel
        """

        result = dict()
        if 'transcripts' not in annotation:
            return result

        result['transcripts'] = annotation['transcripts']
        result['worst_consequence'] = self._get_worst_consequence(result['transcripts'])
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

        if 'transcripts' in annotation:
            annotation.update(TranscriptAnnotation(config.config).process(annotation, genepanel=genepanel))

        if custom_annotation:
            # Merge/overwrite annotation with custom_annotation
            for key in config.config['custom_annotation'].keys():
                if key in custom_annotation:
                    if key not in annotation:
                        annotation[key] = dict()
                    annotation[key].update(custom_annotation[key])

            # References are merged specially
            if 'references' in annotation and 'references' in custom_annotation:
                for ca_ref in custom_annotation['references']:
                    if "source_info" not in ca_ref:
                        ca_ref["source_info"] = dict()

                    # A reference can come from several sources, if so only merge the source
                    assert ca_ref.get('id') or ca_ref.get('pubmed_id'), ca_ref
                    existing_ref = None
                    for r in annotation['references']:
                        for id in ['id', 'pubmed_id']:
                            if r.get(id) is not None and r.get(id) == ca_ref.get(id):
                                existing_ref = r
                                break

                    if existing_ref is not None:
                        existing_ref['sources'] = existing_ref['sources'] + ca_ref['sources']
                        continue

                    annotation['references'].append(ca_ref)

        return annotation
