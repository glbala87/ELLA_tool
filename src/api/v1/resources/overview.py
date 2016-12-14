import datetime
from collections import defaultdict
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import contains_eager
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene

from api import schemas, ApiError
from api.util.util import request_json
from api.v1.resource import Resource
from api.v1 import queries

from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader

from api.config import config


class OverviewAlleleResource(Resource):

    def get_alleles_no_alleleassessment(self, session):
        """
        Returns a list of (allele + genepanel) that are missing alleleinterpretations.

        We only return alleles that:
            - Are missing valid alleleassessments (i.e not outdated if applicable)
            - Are connected to analyses that haven't been finalized.
            - Would not be part of the excluded_alleles for an analysisinterpretation,
              i.e that they are not frequency, intronic or gene filtered.

        Returns [{'genepanel': {'name': ..., 'version': ...}, 'allele': {...alleledata...}}, ...]
        """

        allele_ids_with_valid_aa = queries.allele_ids_with_valid_alleleassessments(session)
        allele_ids_non_finalized_analyses = queries.allele_ids_nonfinalized_analyses(session)

        candidate_allele_ids = session.query(allele.Allele.id).filter(
            allele.Allele.id.in_(allele_ids_non_finalized_analyses),
            ~allele.Allele.id.in_(allele_ids_with_valid_aa)
        ).all()

        candidate_allele_ids = [a[0] for a in candidate_allele_ids]

        return self.load_and_exclude_alleles(session, candidate_allele_ids)

    def load_and_exclude_alleles(self, session, allele_ids):
        """
        Loads alleles using AlleleDataLoader and filters out the FREQUENCY, INTRONIC and GENE filtered variants.

        For the filtering we need to use a genepanel, and one allele can belong to several analyses,
        so in practice we can have multiple gene panels per allele. Hence, the result returns
        a genepanel for each allele, meaning that an allele may appear twice in the resulting list.
        """
        # TODO: Major performance problem when many alleles..ideally we want to do all filtering in SQL.
        #       That's entirely possible, just quite a bit of work.

        # Complicated stuff... :-(

        # Get a list of candidate genepanels per allele id
        allele_ids_genepanels = session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            allele.Allele.id.in_(allele_ids),
            sample.Analysis.genepanel_name == gene.Genepanel.name,
            sample.Analysis.genepanel_version == gene.Genepanel.version,
        ).all()

        # Make a dict of (gp_name, gp_version): [allele_ids], since we must process as many alleles as possible at once with AlleleDataLoader
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        idl = InterpretationDataLoader(session, config)  # Filter function are here for now...
        candidate_alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()
        genepanel_cache = dict()  # Cache for the genepanels. Ideally we'd like to just prefetch them all in single query, but turned out to be hard
        final_alleles = list()

        # Load oldest analysis for each allele, to get the oldest datetime
        # for the analysis awaiting this allele's classification
        allele_ids_deposit_date = session.query(allele.Allele.id, func.min(sample.Analysis.deposit_date)).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            allele.Allele.id.in_(allele_ids)
        ).group_by(allele.Allele.id).all()

        allele_ids_deposit_date = {k: v for k, v in allele_ids_deposit_date}

        for gp_key, check_allele_ids in gp_allele_ids.iteritems():
            if gp_key not in genepanel_cache:
                genepanel_cache[gp_key] = session.query(gene.Genepanel).filter(
                    gene.Genepanel.name == gp_key[0],
                    gene.Genepanel.version == gp_key[1]
                ).one()
            genepanel = genepanel_cache[gp_key]
            genepanel_alleles = [a for a in candidate_alleles if a.id in check_allele_ids]
            loaded_genepanel_alleles = AlleleDataLoader(session).from_objs(  # This is the performance bottleneck...
                genepanel_alleles,
                genepanel=genepanel,
                include_custom_annotation=False,  # Extra data not needed for the filtering we're going to do
                include_reference_assessments=False,
                include_allele_report=False
            )

            for a in loaded_genepanel_alleles:
                if not any([idl._exclude_class1(a), idl._exclude_gene(a), idl._exclude_intronic(a)]):
                    final_alleles.append({'genepanel': {'name': genepanel.name, 'version': genepanel.version}, 'allele': a, 'oldest_analysis': allele_ids_deposit_date[a['id']].isoformat()})
        return final_alleles

    def get_alleles_missing_interpretation(self, session, alleles):
        allele_ids = [a['allele']['id'] for a in alleles]
        allele_ids_missing_interpretations = session.query(allele.Allele.id).filter(
            allele.Allele.id.in_(allele_ids),
            ~allele.Allele.id.in_(session.query(workflow.AlleleInterpretation.allele_id))
        ).all()
        allele_ids_missing_interpretations = [a[0] for a in allele_ids_missing_interpretations]
        return [a for a in alleles if a['allele']['id'] in allele_ids_missing_interpretations]

    def get_alleles_marked_review(self, session, alleles):
        # We assume marked for review when at least one alleleinterpretation is 'Done', and one is 'Not started'
        allele_ids = [a['allele']['id'] for a in alleles]
        allele_ids_markreview = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.id.in_(
                session.query(workflow.AlleleInterpretation.id).filter(
                    workflow.AlleleInterpretation.status == 'Done'
                )
            ),
            workflow.AlleleInterpretation.id.in_(
                session.query(workflow.AlleleInterpretation.id).filter(
                    workflow.AlleleInterpretation.status == 'Not started'
                )
            ),
            workflow.AlleleInterpretation.allele_id.in_(allele_ids)
        ).all()
        allele_ids_markreview = [a[0] for a in allele_ids_markreview]

        return [a for a in alleles if a['allele']['id'] in allele_ids_markreview]


    def get_categorized_analyses(self, session):

        # Get all (analysis_id, allele_id) combinations for analyses that are 'Not started'.
        # We want to categorize these analyses into with_findings, without_findings and missing_alleleassessments
        # based on the state of their alleles' alleleassessments

        # First get rid of all variants that would be filtered out, per analysis

        analysis_ids_not_started = queries.analysis_ids_not_started(session)
        analysis_ids_allele_ids = session.query(sample.Analysis.id, allele.Allele.id).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
        ).filter(
            sample.Analysis.id.in_(analysis_ids_not_started)
        ).all()

        # Now we have all the alleles, so what remains is to see which alleles are
        # filtered out, which have findings, which are normal and which are without alleleassessments
        # For performance, we first categorize allele ids, then connect them to the analyses afterwards
        all_allele_ids = [a[1] for a in analysis_ids_allele_ids]

        # Filter out alleles (it also loads the data, which we don't really need here)
        genepanels_alleles = self.load_and_exclude_alleles(session, all_allele_ids)

        filtered_allele_ids = list(set([a['allele']['id'] for a in genepanels_alleles]))

        classification_options = config['classification']['options']
        classification_findings = [o['value'] for o in classification_options if o.get('include_analysis_with_findings')]
        classification_wo_findings = [o['value'] for o in classification_options if not o.get('include_analysis_with_findings')]

        categorized_allele_ids = {

            'with_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'without_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_wo_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'missing_alleleassessments': session.query(allele.Allele.id).outerjoin(assessment.AlleleAssessment).filter(
                allele.Allele.id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.allele_id.is_(None)
            ).all()

        }

        # Strip out the tuples..
        categorized_allele_ids = {k: [a[0] for a in v] for k, v in categorized_allele_ids.iteritems()}

        # Now we can check our analyses and categorize them
        # Sort into {analysis_id: [allele_ids]}
        analysis_ids_allele_ids_map = defaultdict(list)
        for a in analysis_ids_allele_ids:
            if a[1] in filtered_allele_ids:
                analysis_ids_allele_ids_map[a[0]].append(a[1])

        analyses_not_started = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_(analysis_ids_not_started)
        ).all()
        aschema = schemas.AnalysisSchema()
        analyses_not_started_serialized = [aschema.dump(a).data for a in analyses_not_started]

        final_analyses = {
            'with_findings': [],
            'without_findings': [],
            'missing_alleleassessments': []
        }

        for analysis_id, allele_ids in analysis_ids_allele_ids_map.iteritems():
            analysis = next(a for a in analyses_not_started_serialized if a['id'] == analysis_id)
            if any(a in categorized_allele_ids['missing_alleleassessments'] for a in allele_ids):
                final_analyses['missing_alleleassessments'].append(analysis)
            elif any(a in categorized_allele_ids['with_findings'] for a in allele_ids):
                final_analyses['with_findings'].append(analysis)
            elif all(a in categorized_allele_ids['without_findings'] for a in allele_ids):
                final_analyses['without_findings'].append(analysis)
            else:
                raise ApiError("Allele was not categorized correctly. This may indicate a bug.")

        # Add mark review analyses
        analyses_marked_review = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_(queries.analysis_ids_marked_review(session))
        ).all()
        final_analyses['marked_review'] = [aschema.dump(a).data for a in analyses_marked_review]

        return final_analyses

    def get(self, session):

        alleles_no_alleleassessment = self.get_alleles_no_alleleassessment(session)
        return {
            'alleles': {
                'missing_alleleassessment': self.get_alleles_missing_interpretation(session, alleles_no_alleleassessment),
                'marked_review': self.get_alleles_marked_review(session, alleles_no_alleleassessment)
            },
            'analyses': self.get_categorized_analyses(session)
        }, 200

if __name__ == '__main__':
    from vardb.util import DB
    db = DB()
    db.connect()

    import json
    print json.dumps(OverviewAlleleInterpretationResource().get(db.session)[0])