import datetime
import itertools
import pytz
from collections import defaultdict

from sqlalchemy import tuple_, or_
from sqlalchemy.orm import joinedload

from vardb.datamodel import user, assessment, sample, genotype, allele, workflow, gene

from api import schemas, ApiError, ConflictError
from api.util.allelefilter import AlleleFilter
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.snapshotcreator import SnapshotCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.util import queries


def _check_interpretation_input(allele, analysis):
    if allele is None and analysis is None:
        raise RuntimeError("One of arguments allele or analysis is required.")


def _get_interpretation_model(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretation
    if analysis is not None:
        return workflow.AnalysisInterpretation


def _get_interpretation_model_field(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretation.allele_id
    if analysis is not None:
        return workflow.AnalysisInterpretation.analysis_id


def _get_interpretationsnapshot_model(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretationSnapshot
    if analysis is not None:
        return workflow.AnalysisInterpretationSnapshot


def _get_interpretationsnapshot_field(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretationSnapshot.alleleinterpretation_id
    if analysis is not None:
        return workflow.AnalysisInterpretationSnapshot.analysisinterpretation_id


def _get_snapshotcreator_mode(allele, analysis):
    if allele is not None:
        return 'allele'
    elif analysis is not None:
        return 'analysis'


def _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id):
    if alleleinterpretation_id is not None:
        return alleleinterpretation_id
    if analysisinterpretation_id is not None:
        return analysisinterpretation_id


def _get_latest_interpretation(session, allele_id, analysis_id):
    model = _get_interpretation_model(allele_id, analysis_id)
    field = _get_interpretation_model_field(allele_id, analysis_id)
    if allele_id is not None:
        model_id = allele_id
    elif analysis_id is not None:
        model_id = analysis_id
    return session.query(model).filter(
        field == model_id,
    ).order_by(model.id.desc()).first()


def get_alleles(session, allele_ids, genepanels, alleleinterpretation_id=None, analysisinterpretation_id=None, current_allele_data=False):
    """
    Loads all alleles for an interpretation. The interpretation model is dynamically chosen
    based on which argument (alleleinterpretation_id, analysisinterpretation_id) is given.

    If current_allele_data is True, load newest allele data instead of allele data
    at time of interpretation snapshot.

    By default, the latest connected data is loaded (e.g. latest annotations, assessments etc).
    However, if the interpretation is marked as 'Done', it's context is loaded from the snapshot,
    so any annotation, alleleassessments etc for each allele will be what was stored
    at the time of finishing the interpretation.
    """

    _check_interpretation_input(alleleinterpretation_id, analysisinterpretation_id)

    alleles = session.query(allele.Allele).filter(
        allele.Allele.id.in_(allele_ids)
    ).all()

    # Get interpretation to get genepanel and check status
    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(alleleinterpretation_id, analysisinterpretation_id)
    interpretationsnapshot_model = _get_interpretationsnapshot_model(alleleinterpretation_id, analysisinterpretation_id)
    interpretationsnapshot_field = _get_interpretationsnapshot_field(alleleinterpretation_id, analysisinterpretation_id)

    interpretation = session.query(interpretation_model).filter(
        interpretation_model.id == interpretation_id,
        tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
    ).one()

    link_filter = None  # In case of loading specific data rather than latest available for annotation, custom_annotation etc..
    if not current_allele_data and interpretation.status == 'Done':
        # Serve using context data from snapshot
        snapshots = session.query(interpretationsnapshot_model).filter(
            interpretationsnapshot_field == interpretation.id
        ).all()

        link_filter = {
            'annotation_id': [s.annotation_id for s in snapshots if s.annotation_id is not None],
            'customannotation_id': [s.customannotation_id for s in snapshots if s.customannotation_id is not None],
            'alleleassessment_id': [s.presented_alleleassessment_id for s in snapshots if s.presented_alleleassessment_id is not None],
            'allelereport_id': [s.presented_allelereport_id for s in snapshots if s.presented_allelereport_id is not None],
        }

        # For historical referenceassessments, they should all be connected to the alleleassessments used
        ra_ids = session.query(assessment.ReferenceAssessment.id).join(
            assessment.AlleleAssessment.referenceassessments
        ).filter(
            assessment.AlleleAssessment.id.in_(link_filter['alleleassessment_id'])
        ).all()
        link_filter['referenceassessment_id'] = [i[0] for i in ra_ids]

    # Only relevant for analysisinterpretation: Include the genotype for connected samples
    sample_ids = list()
    if analysisinterpretation_id is not None:

        sample_ids = session.query(sample.Sample.id).filter(
            sample.Sample.analysis_id == sample.Analysis.id,
            sample.Analysis.id == interpretation.analysis_id  # We know interpretation is analysisinterpretation
        ).all()

        sample_ids = [s[0] for s in sample_ids]

    kwargs = {
        'include_annotation': True,
        'include_custom_annotation': True,
        'genepanel': interpretation.genepanel
    }

    if link_filter:
        kwargs['link_filter'] = link_filter
    if sample_ids:
        kwargs['include_genotype_samples'] = sample_ids
    return AlleleDataLoader(session).from_objs(
        alleles,
        **kwargs
    )


def load_genepanel_for_allele_ids(session, allele_ids, gp_name, gp_version):
    """
    Loads genepanel data using input allele_ids as filter
    for what transcripts and phenotypes to include.
    """
    genepanel = session.query(gene.Genepanel).filter(
        gene.Genepanel.name == gp_name,
        gene.Genepanel.version == gp_version
    ).one()

    alleles_filtered_genepanel = queries.annotation_transcripts_genepanel(
        session,
        allele_ids,
        [(gp_name, gp_version)]
    ).subquery()

    transcripts = session.query(gene.Transcript).options(joinedload(gene.Transcript.gene)).join(
        gene.Genepanel.transcripts
    ).filter(
        gene.Transcript.transcript_name == alleles_filtered_genepanel.c.genepanel_transcript
    ).all()

    phenotypes = session.query(gene.Phenotype).filter(
        gene.Transcript.transcript_name == alleles_filtered_genepanel.c.genepanel_transcript,
        gene.Phenotype.gene_id == gene.Transcript.gene_id,
        gene.Phenotype.genepanel_name == gp_name,
        gene.Phenotype.genepanel_version == gp_version
    ).all()

    genepanel_data = schemas.GenepanelSchema().dump(genepanel).data
    genepanel_data['transcripts'] = schemas.TranscriptSchema().dump(transcripts, many=True).data
    genepanel_data['phenotypes'] = schemas.PhenotypeSchema().dump(phenotypes, many=True).data
    return genepanel_data


def update_interpretation(session, user_id, data, alleleinterpretation_id=None, analysisinterpretation_id=None):
    """
    Updates the current interpretation inplace.

    **Only allowed for interpretations that are `Ongoing`**

    """

    def update_history(interpretation):
        if 'history' not in interpretation.state_history:
            interpretation.state_history['history'] = list()
        interpretation.state_history['history'].insert(0, {
            'time': datetime.datetime.now(pytz.utc).isoformat(),
            'state': interpretation.state,
            'user_id': interpretation.user_id
        })

    def check_update_allowed(interpretation, user_id, patch_data):
        if interpretation.status == 'Done':
            raise ConflictError("Cannot PATCH interpretation with status 'DONE'")
        elif interpretation.status == 'Not started':
            raise ConflictError("Interpretation not started. Call it's analysis' start action to begin interpretation.")

        # Check that user is same as before
        if interpretation.user_id:
            if interpretation.user_id != user_id:
                current_user = session.query(user.User).filter(user.User.id == user_id).one()
                interpretation_user = session.query(user.User).filter(user.User.id == interpretation.user_id).one()
                raise ConflictError(u"Interpretation owned by {} {} cannot be updated by other user ({} {})"
                               .format(interpretation_user.first_name, interpretation.user.last_name, current_user.first_name, current_user.last_name))

    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(alleleinterpretation_id, analysisinterpretation_id)

    interpretation = session.query(interpretation_model).filter(
        interpretation_model.id == interpretation_id
    ).one()

    check_update_allowed(interpretation, user_id, data)

    # Add current state to history if new state is different:
    if data['state'] != interpretation.state:
        update_history(interpretation)

    # Overwrite state fields with new values
    interpretation.state = data['state']
    interpretation.user_state = data['user_state']
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)
    return interpretation


def get_interpretation(session, genepanels, alleleinterpretation_id=None, analysisinterpretation_id=None):
    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(alleleinterpretation_id, analysisinterpretation_id)

    interpretation = session.query(interpretation_model).filter(
        interpretation_model.id == interpretation_id,
        tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
    ).one()

    idl = InterpretationDataLoader(session)
    obj = idl.from_obj(interpretation)
    return obj


def get_interpretations(session, genepanels, allele_id=None, analysis_id=None):

    interpretation_model = _get_interpretation_model(allele_id, analysis_id)
    interpretation_model_field = _get_interpretation_model_field(allele_id, analysis_id)

    if allele_id is not None:
        model_id = allele_id
    elif analysis_id is not None:
        model_id = analysis_id

    interpretations = session.query(interpretation_model).filter(
        interpretation_model_field == model_id,
        tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
    ).order_by(interpretation_model.id).all()

    loaded_interpretations = list()
    idl = InterpretationDataLoader(session)

    for interpretation in interpretations:
        loaded_interpretations.append(idl.from_obj(interpretation))

    return loaded_interpretations


def override_interpretation(session, user_id, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    new_user = session.query(user.User).filter(
        user.User.id == user_id
    ).one()

    if interpretation.status != 'Ongoing':
        raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = new_user
    return interpretation


def start_interpretation(session, user_id, data, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    start_user = session.query(user.User).filter(
        user.User.id == user_id
    ).one()

    if not interpretation:
        interpretation_model = _get_interpretation_model(allele_id, analysis_id)
        interpretation = interpretation_model()
        if allele_id is not None:
            interpretation.allele_id = allele_id
        elif analysis_id is not None:
            interpretation.analysis_id = analysis_id

        session.add(interpretation)

    elif interpretation.status != 'Not started':
        raise ApiError("Cannot start existing interpretation where status = {}".format(interpretation.status))

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = start_user
    interpretation.status = 'Ongoing'
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    if analysis_id is not None:
        analysis = session.query(sample.Analysis).filter(
            sample.Analysis.id == analysis_id
        ).one()
        interpretation.genepanel = analysis.genepanel
    elif allele_id is not None:
        # For allele workflow, the user can choose genepanel context for each interpretation
        interpretation.genepanel_name = data['gp_name']
        interpretation.genepanel_version = data['gp_version']
    else:
        raise RuntimeError("Missing id argument")

    return interpretation


def markreview_interpretation(session, data, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)
    interpretation_model = _get_interpretation_model(allele_id, analysis_id)

    if not interpretation.status == 'Ongoing':
        raise ApiError("Cannot mark for review when latest interpretation is not 'Ongoing'")

    # We must load it _before_ we create assessments, since assessments
    # can affect the filtering (e.g. alleleassessments created for filtered alleles)
    loaded_interpretation = InterpretationDataLoader(session).from_obj(interpretation)

    presented_alleleassessment_ids = [a['presented_alleleassessment_id'] for a in data['alleleassessments'] if 'presented_alleleassessment_id' in a]
    presented_alleleassessments = session.query(assessment.AlleleAssessment).filter(
        assessment.AlleleAssessment.id.in_(presented_alleleassessment_ids)
    ).all()

    presented_allelereport_ids = [a['presented_allelereport_id'] for a in data['allelereports'] if 'presented_allelereport_id' in a]
    presented_allelereports = session.query(assessment.AlleleReport).filter(
        assessment.AlleleAssessment.id.in_(presented_allelereport_ids)
    ).all()

    snapshot_objects = SnapshotCreator(session).create_from_data(
        _get_snapshotcreator_mode(allele_id, analysis_id),
        loaded_interpretation,
        data['annotations'],
        presented_alleleassessments,
        presented_allelereports,
        custom_annotations=data.get('custom_annotations'),
    )

    session.add_all(snapshot_objects)

    interpretation.status = 'Done'
    interpretation.end_action = 'Mark review'
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    # Create next interpretation
    interpretation_next = interpretation_model.create_next(interpretation)
    session.add(interpretation_next)

    return interpretation, interpretation_next


def reopen_interpretation(session, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)
    interpretation_model = _get_interpretation_model(allele_id, analysis_id)

    if interpretation is None:
        raise ApiError("There are no existing interpretations for this item. Use the start action instead.")

    if not interpretation.status == 'Done':
        raise ApiError("Interpretation is already 'Not started' or 'Ongoing'. Cannot reopen.")

    # Create next interpretation
    interpretation_next = interpretation_model.create_next(interpretation)
    session.add(interpretation_next)

    return interpretation, interpretation_next


def finalize_interpretation(session, user_id, data, allele_id=None, analysis_id=None):
    """
    Finalizes an interpretation.

    This sets the allele/analysis' current interpretation's status to `Done` and creates
    any [alleleassessment|referenceassessment|allelereport] objects for the provided alleles,
    unless it's specified to reuse existing objects.

    The user must provide a list of alleleassessments, referenceassessments and allelereports.
    For each assessment/report, there are two cases:
    - 'reuse=False' or reuse is missing: a new assessment/report is created in the database using the data given.
    - 'reuse=True' The id of an existing assessment/report is expected in 'presented_assessment_id'
        or 'presented_report_id'.

    The assessment/report mentioned in the 'presented..' field is the one displayed/presented to the user.
    We pass it along to keep a record of the context of the assessment.

    The analysis will be linked to assessments/report.

    **Only works for analyses with a `Ongoing` current interpretation**
    """

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    if not interpretation.status == 'Ongoing':
        raise ApiError("Cannot finalize when latest interpretation is not 'Ongoing'")

    # We must load it _before_ we create assessments, since assessments
    # can affect the filtering (e.g. alleleassessments created for filtered alleles)
    loaded_interpretation = InterpretationDataLoader(session).from_obj(interpretation)

    # Create/reuse assessments
    grouped_alleleassessments = AssessmentCreator(session).create_from_data(
        user_id,
        data['annotations'],
        data['alleleassessments'],
        data['custom_annotations'],
        data['referenceassessments'],
        data['attachments']
    )

    reused_alleleassessments = grouped_alleleassessments['alleleassessments']['reused']
    created_alleleassessments = grouped_alleleassessments['alleleassessments']['created']

    session.add_all(created_alleleassessments)

    # Create/reuse allelereports
    all_alleleassessments = reused_alleleassessments + created_alleleassessments
    grouped_allelereports = AlleleReportCreator(session).create_from_data(
        user_id,
        data['allelereports'],
        all_alleleassessments
    )

    reused_allelereports = grouped_allelereports['reused']
    created_allelereports = grouped_allelereports['created']

    session.add_all(created_allelereports)

    # Create interpretation snapshot objects
    presented_alleleassessment_ids = [a['presented_alleleassessment_id'] for a in data['alleleassessments'] if 'presented_alleleassessment_id' in a]
    presented_alleleassessments = session.query(assessment.AlleleAssessment).filter(
        assessment.AlleleAssessment.id.in_(presented_alleleassessment_ids)
    ).all()

    presented_allelereport_ids = [a['presented_allelereport_id'] for a in data['allelereports'] if 'presented_allelereport_id' in a]
    presented_allelereports = session.query(assessment.AlleleReport).filter(
        assessment.AlleleReport.id.in_(presented_allelereport_ids)
    ).all()

    snapshot_objects = SnapshotCreator(session).create_from_data(
        _get_snapshotcreator_mode(allele_id, analysis_id),
        loaded_interpretation,
        data['annotations'],
        presented_alleleassessments,
        presented_allelereports,
        used_alleleassessments=created_alleleassessments + reused_alleleassessments,
        used_allelereports=created_allelereports + reused_allelereports,
        custom_annotations=data.get('custom_annotations')
    )

    session.add_all(snapshot_objects)

    # Update interpretation and return data
    interpretation.status = 'Done'
    interpretation.end_action = 'Finalize'
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    reused_referenceassessments = grouped_alleleassessments['referenceassessments']['reused']
    created_referenceassessments = grouped_alleleassessments['referenceassessments']['created']

    session.add_all(created_referenceassessments)

    all_referenceassessments = reused_referenceassessments + created_referenceassessments
    all_allelereports = reused_allelereports + created_allelereports

    return {
        'allelereports': schemas.AlleleReportSchema().dump(
            all_allelereports, many=True).data,
        'alleleassessments': schemas.AlleleAssessmentSchema().dump(
            all_alleleassessments, many=True).data,
        'referenceassessments': schemas.ReferenceAssessmentSchema().dump(all_referenceassessments,
                                                                         many=True).data,
    }


def get_genepanels(session, allele_ids, user=None):
    """
    Get all genepanels overlapping the transcripts of the provided allele_ids.

    Is user is provided, the genepanels are restricted to the user group's panels.
    """
    if user:
        gp_keys = [(g.name, g.version) for g in user.group.genepanels]
    else:
        gp_keys = session.query(gene.Genepanel.name, gene.Genepanel.version).all()

    alleles_genepanels = queries.alleles_transcript_filtered_genepanel(
        session,
        allele_ids,
        gp_keys,
        None
    )
    alleles_genepanels = alleles_genepanels.subquery()

    candidate_genepanels = session.query(
        alleles_genepanels.c.name,
        alleles_genepanels.c.version
    ).distinct().all()


    # TODO: Sort by previously used interpretations

    result = schemas.GenepanelSchema().dump(candidate_genepanels, many=True)
    return result


def get_workflow_allele_collisions(session, allele_ids, analysis_id=None, allele_id=None):
    """
    Check for possible collisions in other allele or analysis workflows,
    which happens to have overlapping alleles with the ids given in 'allele_ids'.

    If you're checking a specifc workflow, include the analysis_id or allele_id argument
    to specify which workflow to exclude from the check.
    For instance, if you want to check analysis 3, having e.g. 20 alleles, you don't want
    to include analysis 3 in the collision check as it's not informative
    to see a collision with itself. You would pass in analysis_id=3 to exclude it.
    """

    # Remove if you need to check collisions in general
    assert (analysis_id is not None) or (allele_id is not None), "No object passed to compute collisions with"

    # Get all analysis workflows that are either Ongoing, or waiting for review
    # i.e having not only 'Not started' interpretations or not only 'Done' interpretations.
    workflow_analysis_ids = session.query(sample.Analysis.id).filter(
        or_(
            sample.Analysis.id.in_(queries.workflow_analyses_marked_review(session)),
            sample.Analysis.id.in_(queries.workflow_analyses_ongoing(session)),
        )
    )

    # Exclude "ourself" if applicable
    if analysis_id is not None:
        workflow_analysis_ids = workflow_analysis_ids.filter(
            sample.Analysis.id != analysis_id
        )

    # Get all allele ids con        nected to analysis workflows that are ongoing
    wf_analysis_gp_allele_ids = session.query(
        workflow.AnalysisInterpretation.genepanel_name,
        workflow.AnalysisInterpretation.genepanel_version,
        workflow.AnalysisInterpretation.user_id,
        allele.Allele.id
    ).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis,
        workflow.AnalysisInterpretation
    ).filter(
        sample.Analysis.id.in_(workflow_analysis_ids),
        allele.Allele.id.in_(allele_ids),
        workflow.AnalysisInterpretation.status != 'Done'
    ).distinct()

    # Get all allele ids connected to allele workflows that are ongoing
    wf_allele_gp_allele_ids = session.query(
        workflow.AlleleInterpretation.genepanel_name,
        workflow.AlleleInterpretation.genepanel_version,
        workflow.AlleleInterpretation.user_id,
        workflow.AlleleInterpretation.allele_id,
    ).filter(
        or_(
            workflow.AlleleInterpretation.allele_id.in_(queries.workflow_alleles_marked_review(session)),
            workflow.AlleleInterpretation.allele_id.in_(queries.workflow_alleles_ongoing(session))
        ),
        workflow.AlleleInterpretation.status != 'Done',
        workflow.AlleleInterpretation.allele_id.in_(allele_ids)
    ).distinct()

    # Exclude "ourself" if applicable
    if allele_id is not None:
        wf_allele_gp_allele_ids = wf_allele_gp_allele_ids.filter(
            workflow.AlleleInterpretation.allele_id != allele_id
        )

    # Next, we need to filter the alleles so we don't report collisions
    # on alleles that would anyways be filtered out.
    # Organize by genepanel for correct filtering.
    # Also, keep track of which user had which variant, so we can
    # report that as well.
    total_gp_allele_ids = defaultdict(set)  # {('HBOC', 'v01'): [1, 2, 3, ...], ...}
    user_ids = set()
    wf_analysis_gp_allele_ids = wf_analysis_gp_allele_ids.all()
    wf_allele_gp_allele_ids = wf_allele_gp_allele_ids.all()

    for gp_name, gp_version, user_id, al_id in itertools.chain(wf_allele_gp_allele_ids, wf_analysis_gp_allele_ids):
        gp_key = (gp_name, gp_version)
        total_gp_allele_ids[gp_key].add(al_id)
        user_ids.add(user_id)

    af = AlleleFilter(session)
    nonfiltered_gp_allele_ids = af.filter_alleles(total_gp_allele_ids)

    # For performance we have to jump through some hoops...
    # First we load in all allele data in one query
    nonfiltered_allele_ids = itertools.chain(*[v['allele_ids'] for v in nonfiltered_gp_allele_ids.values()])
    collision_alleles = session.query(allele.Allele).filter(
        allele.Allele.id.in_(nonfiltered_allele_ids),
    ).all()

    # Next load the alleles by their genepanel to load with AlleleDataLoader
    # using the correct genepanel for those alleles.
    genepanels = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(total_gp_allele_ids.keys())
    )
    adl = AlleleDataLoader(session)
    gp_dumped_alleles = dict()
    for gp_key, al_ids in nonfiltered_gp_allele_ids.iteritems():
        genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
        alleles = [a for a in collision_alleles if a.id in al_ids['allele_ids']]
        gp_dumped_alleles[gp_key] = adl.from_objs(
            alleles,
            genepanel=genepanel,
            include_allele_report=False,
            include_custom_annotation=False,
            include_reference_assessments=False,
            include_allele_assessment=False
        )

    # Preload the users
    users = session.query(user.User).filter(
        user.User.id.in_(user_ids)
    ).all()
    dumped_users = schemas.UserSchema().dump(users, many=True).data

    # Finally connect it all together (phew!)
    collisions = list()
    for wf_type, wf_entries in [('allele', wf_allele_gp_allele_ids), ('analysis', wf_analysis_gp_allele_ids)]:
        for gp_name, gp_version, user_id, al_id in wf_entries:
            gp_key = (gp_name, gp_version)
            dumped_allele = next((a for a in gp_dumped_alleles[gp_key] if a['id'] == al_id), None)
            if not dumped_allele:  # Allele might have been filtered out..
                continue
            # If an workflow is in review, it will have no user assigned...
            dumped_user = next((u for u in dumped_users if u['id'] == user_id), None)
            collisions.append({
                'type': wf_type,
                'user': dumped_user,
                'allele': dumped_allele
            })

    return collisions
