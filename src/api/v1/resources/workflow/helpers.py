import datetime

from sqlalchemy import or_

from vardb.datamodel import user, assessment, sample, genotype, allele, workflow

from api import schemas, ApiError
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.snapshotcreator import SnapshotCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.v1 import queries
from api.config import config


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

    return session.query(model).filter(field == model_id).order_by(model.id.desc()).first()


def get_alleles(session, allele_ids, alleleinterpretation_id=None, analysisinterpretation_id=None, current_allele_data=False):
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
        interpretation_model.id == interpretation_id
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


def update_interpretation(session, data, alleleinterpretation_id=None, analysisinterpretation_id=None):
    """
    Updates the current interpretation inplace.

    **Only allowed for interpretations that are `Ongoing`**

    """

    def update_history(interpretation):
        if 'history' not in interpretation.state_history:
            interpretation.state_history['history'] = list()
        interpretation.state_history['history'].insert(0, {
            'time': datetime.datetime.now().isoformat(),
            'state': interpretation.state,
            'user_id': interpretation.user_id
        })

    def check_update_allowed(interpretation, patch_data):
        if interpretation.status == 'Done':
            raise ApiError("Cannot PATCH interpretation with status 'DONE'")
        elif interpretation.status == 'Not started':
            raise ApiError("Interpretation not started. Call it's analysis' start action to begin interpretation.")

        # Check that user is same as before
        if interpretation.user_id:
            if interpretation.user_id != patch_data['user_id']:
                raise ApiError("Interpretation owned by {} cannot be updated by other user ({})"
                               .format(interpretation.user_id, patch_data['user_id']))

    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(alleleinterpretation_id, analysisinterpretation_id)

    interpretation = session.query(interpretation_model).filter(
        interpretation_model.id == interpretation_id
    ).one()

    check_update_allowed(interpretation, data)

    # Add current state to history if new state is different:
    if data['state'] != interpretation.state:
        update_history(interpretation)

    # Overwrite state fields with new values
    interpretation.state = data['state']
    interpretation.user_state = data['user_state']
    interpretation.date_last_update = datetime.datetime.now()
    return interpretation


def get_interpretation(session, alleleinterpretation_id=None, analysisinterpretation_id=None):
    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(alleleinterpretation_id, analysisinterpretation_id)

    interpretation = session.query(interpretation_model).filter(
        interpretation_model.id == interpretation_id
    ).one()

    idl = InterpretationDataLoader(session, config)
    obj = idl.from_obj(interpretation)
    return obj


def get_interpretations(session, allele_id=None, analysis_id=None):

    interpretation_model = _get_interpretation_model(allele_id, analysis_id)
    interpretation_model_field = _get_interpretation_model_field(allele_id, analysis_id)

    if allele_id is not None:
        model_id = allele_id
    elif analysis_id is not None:
        model_id = analysis_id

    interpretations = session.query(interpretation_model).filter(
        interpretation_model_field == model_id
    ).order_by(interpretation_model.id).all()

    loaded_interpretations = list()
    idl = InterpretationDataLoader(session, config)

    for interpretation in interpretations:
        loaded_interpretations.append(idl.from_obj(interpretation))

    return loaded_interpretations


def override_interpretation(session, data, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    new_user = session.query(user.User).filter(
        user.User.id == data['user_id']
    ).one()

    if interpretation.status != 'Ongoing':
        raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = new_user
    return interpretation


def start_interpretation(session, data, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    start_user = session.query(user.User).filter(
        user.User.id == data['user_id']
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
    interpretation.date_last_update = datetime.datetime.now()

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
        interpretation.id,
        data['annotations'],
        presented_alleleassessments,
        presented_allelereports,
        custom_annotations=data.get('custom_annotations'),
    )

    session.add_all(snapshot_objects)

    interpretation.status = 'Done'
    interpretation.date_last_update = datetime.datetime.now()

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


def finalize_interpretation(session, data, allele_id=None, analysis_id=None):
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

    # Create/reuse assessments
    grouped_alleleassessments = AssessmentCreator(session).create_from_data(
        data['annotations'],
        data['alleleassessments'],
        data['custom_annotations'],
        data['referenceassessments']
    )

    reused_alleleassessments = grouped_alleleassessments['alleleassessments']['reused']
    created_alleleassessments = grouped_alleleassessments['alleleassessments']['created']

    session.add_all(created_alleleassessments)

    # Create/reuse allelereports
    all_alleleassessments = reused_alleleassessments + created_alleleassessments
    grouped_allelereports = AlleleReportCreator(session).create_from_data(
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
        interpretation.id,
        data['annotations'],
        presented_alleleassessments,
        presented_allelereports,
        used_alleleassessments=created_alleleassessments + reused_alleleassessments,
        used_allelereports=created_allelereports + reused_allelereports,
        custom_annotations=data.get('custom_annotations'),
    )

    session.add_all(snapshot_objects)

    # Update interpretation and return data
    interpretation.status = 'Done'
    interpretation.date_last_update = datetime.datetime.now()

    reused_referenceassessments = grouped_alleleassessments['referenceassessments']['reused']
    created_referenceassessments = grouped_alleleassessments['referenceassessments']['created']

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


def get_workflow_allele_collisions(session, allele_ids, analysis_id=None, allele_id=None):
    """
    Check for possible collisions in other allele or analysis workflows,
    which happens to have overlapping alleles with the ids given in 'allele_ids'.

    Only alleles without an existing alleleassessment is considered a collision.

    If you're checking a specifc workflow, include the analysis_id or allele_id argument
    to specify which workflow to exclude from the check.
    For instance, if you want to check analysis 3, having e.g. 20 alleles, you don't want
    to include analysis 3 in the collision check as it's not informative
    to see a collision with itself. You would pass in analysis_id=3 to exclude it.
    """

    # Get all analysis workflows that are either Ongoing, or waiting for review
    # i.e having not only 'Not started' interpretations or not only 'Done' interpretations.
    workflow_analysis_ids = session.query(sample.Analysis.id).filter(
        ~sample.Analysis.id.in_(queries.workflow_analyses_finalized(session)),
        ~sample.Analysis.id.in_(queries.workflow_analyses_not_started(session)),
    )

    if analysis_id is not None:
        workflow_analysis_ids = workflow_analysis_ids.filter(
            sample.Analysis.id != analysis_id
        )

    # Get all allele ids connected to analysis workflows that are ongoing
    analysis_alleles_ids = session.query(allele.Allele.id).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(sample.Analysis.id.in_(workflow_analysis_ids))

    # Get all allele ids connected to allele workflows that are ongoing
    # (also ensure at least one AlleleInterpretation exists)
    allele_ids_has_interpretation = session.query(workflow.AlleleInterpretation.allele_id)

    workflow_allele_ids = session.query(allele.Allele.id).filter(
        ~allele.Allele.id.in_(queries.workflow_alleles_finalized(session)),
        ~allele.Allele.id.in_(queries.workflow_alleles_not_started(session)),
        allele.Allele.id.in_(allele_ids_has_interpretation)
    )

    if allele_id is not None:
        workflow_allele_ids = workflow_allele_ids.filter(
            allele.Allele.id != allele_id
        )

    # Compile final list of alleles that are colliding,
    # where we excluded the ones with existing alleleassessment

    has_aa = session.query(assessment.AlleleAssessment.allele_id)

    collision_alleles = session.query(allele.Allele.id).filter(
        or_(allele.Allele.id.in_(analysis_alleles_ids),
            allele.Allele.id.in_(workflow_allele_ids)),
        ~allele.Allele.id.in_(has_aa),
        allele.Allele.id.in_(allele_ids)
    )

    collision_allele_count = collision_alleles.count()

    return {'collisions': {'count': collision_allele_count}}

