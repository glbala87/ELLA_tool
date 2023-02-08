import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Sequence, Set, Tuple, Type, Union, overload

import pytz
from sqlalchemy import and_, func, literal
from sqlalchemy.dialects.postgresql.array import Any
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.schema import Column
from typing_extensions import Literal

from api import ApiError, ConflictError, schemas
from api.schemas.pydantic.v1.config import (
    AlleleFinalizeRequirementsConfig,
    AnalysisFinalizeRequirementsConfig,
    UserConfig,
)
from api.schemas.pydantic.v1.resources import (
    AlleleActionStartRequest,
    CreateInterpretationLogRequest,
    FinalizeAlleleRequest,
    MarkAlleleInterpretationRequest,
    MarkAnalysisInterpretationRequest,
    PatchInterpretationRequest,
)
from api.schemas.pydantic.v1.workflow import AlleleCollision, OngoingWorkflow
from api.util.types import CallerTypes, FilteredAlleleCategories, WorkflowTypes
from datalayer import (
    AlleleDataLoader,
    AlleleFilter,
    AlleleReportCreator,
    AssessmentCreator,
    SnapshotCreator,
    filters,
    queries,
)
from vardb.datamodel import allele, annotation, assessment, gene, genotype, sample, user, workflow

### Magic Metadata

_Interp = Union[workflow.AlleleInterpretation, workflow.AnalysisInterpretation]
_InterpType = Union[
    Type[workflow.AlleleInterpretation],
    Type[workflow.AnalysisInterpretation],
]
_SnapshotType = Union[
    Type[workflow.AlleleInterpretationSnapshot],
    Type[workflow.AnalysisInterpretationSnapshot],
]
_InterpSchema = Union[
    Type[schemas.AlleleInterpretationSchema],
    Type[schemas.AnalysisInterpretationSchema],
]

_MarkInterpretationRequest = Union[
    MarkAlleleInterpretationRequest, MarkAnalysisInterpretationRequest
]


@dataclass(frozen=True)
class InterpretationMetadata:
    name: WorkflowTypes
    model: _InterpType
    snapshot: _SnapshotType
    schema: _InterpSchema

    @property
    def model_id_field(self) -> str:
        return f"{self.name}_id"

    @property
    def snapshot_id_field(self) -> str:
        return f"{self.name}interpretation_id"

    @property
    def model_id(self) -> Column:
        "gets Column object for the model type being interpreted"
        return getattr(self.model, self.model_id_field)

    @property
    def snapshot_id(self) -> Column:
        return getattr(self.snapshot, self.snapshot_id_field)

    def get_latest_interpretation(self, session: Session, model_id: int):
        return (
            session.query(self.model)
            .filter(self.model_id == model_id)
            .order_by(self.model.date_created.desc())
            .first()
        )

    def get_interpretation(
        self,
        session: Session,
        interpretation_id: int,
        genepanels: Optional[Sequence[gene.Genepanel]] = None,
    ):
        "returns interpretation by unique id, optionally filtering by Genepanel"
        q = session.query(self.model).filter(self.model.id == interpretation_id)
        if genepanels:
            q = q.filter(self._genepanel_filter(session, genepanels))
        return q.one()

    def get_model_interpretations(
        self,
        session: Session,
        model_id: int,
        genepanels: Optional[Sequence[gene.Genepanel]] = None,
    ):
        "gets all interpretations for the model id, optionally filtering by Genepanel"
        q = session.query(self.model).filter(self.model_id == model_id)
        if genepanels:
            q = q.filter(self._genepanel_filter(session, genepanels))
        return q.order_by(self.model.id).all()

    def get_snapshots(self, session: Session, snap_id: int):
        return session.query(self.snapshot).filter(self.snapshot_id == snap_id).all()

    def _genepanel_filter(self, session: Session, genepanels: Sequence[gene.Genepanel]):
        return filters.in_(
            session,
            (self.model.genepanel_name, self.model.genepanel_version),
            [(gp.name, gp.version) for gp in genepanels],
        )


AlleleInterpretationMeta = InterpretationMetadata(
    name=WorkflowTypes.ALLELE,
    model=workflow.AlleleInterpretation,
    snapshot=workflow.AlleleInterpretationSnapshot,
    schema=schemas.AlleleInterpretationSchema,
)

AnalysisInterpretationMeta = InterpretationMetadata(
    name=WorkflowTypes.ANALYSIS,
    model=workflow.AnalysisInterpretation,
    snapshot=workflow.AnalysisInterpretationSnapshot,
    schema=schemas.AnalysisInterpretationSchema,
)

###


# explicit keywords required when calling. values given can also refer to *interpretation_id
def _get_interpretation_meta(
    *,
    allele_id: int = None,
    analysis_id: int = None,
):
    """
    returns id and InterpretationMetadata object for either AlleleInterpretation or AnalysisInterpretation
    """
    if all([allele_id, analysis_id]) or not any([i is not None for i in [allele_id, analysis_id]]):
        raise ValueError("Must specify one of: allele_id, analysis_id")
    elif allele_id is not None:
        return allele_id, AlleleInterpretationMeta
    elif analysis_id is not None:
        return analysis_id, AnalysisInterpretationMeta
    else:
        raise ValueError("This should never happen")


def _get_uncommitted_interpretation_ids(session: Session, meta: InterpretationMetadata) -> Set[int]:
    """
    Get all analysis/allele ids for workflows that have an interpretation that may contain
    work that is not commited.
    Criteria:
    1. Include if more than one interpretation and latest is not finalized.
    The first criterion (more than one) is due to single interpretations
    may be in 'Not started' status and we don't want to include those.
    2. In addition, include all Ongoing interpretations. These will naturally
    contain uncommited work. This case is partly covered in 1. above, but not
    for single interpretations.
    """

    more_than_one = (
        session.query(meta.model_id)
        .group_by(meta.model_id)
        .having(func.count(meta.model_id) > 1)
        .subquery()
    )

    ongoing = set(
        queries.workflow_by_status(
            session,
            meta.model,
            meta.model_id_field,
            status="Ongoing",
        ).scalar_all()
    )

    not_finalized = queries.workflow_by_status(
        session, meta.model, meta.model_id_field, finalized=False
    ).subquery()

    more_than_one_not_finalized = set(
        session.query(getattr(more_than_one.c, meta.model_id_field))
        .join(
            not_finalized,
            getattr(not_finalized.c, meta.model_id_field)
            == getattr(more_than_one.c, meta.model_id_field),
        )
        .distinct()
        .scalar_all()
    )

    return ongoing | more_than_one_not_finalized


def get_alleles(
    session: Session,
    allele_ids: Sequence[int],
    genepanels: Sequence[gene.Genepanel],
    *,
    alleleinterpretation_id: int = None,
    analysisinterpretation_id: int = None,
    current_allele_data: bool = False,
    filterconfig_id: int = None,
):
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

    alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()

    # Get interpretation to get genepanel and check status
    interpretation_id, meta = _get_interpretation_meta(
        allele_id=alleleinterpretation_id,
        analysis_id=analysisinterpretation_id,
    )

    interpretation = meta.get_interpretation(session, interpretation_id, genepanels)

    link_filter = None  # In case of loading specific data rather than latest available for annotation, custom_annotation etc..
    if not current_allele_data and interpretation.status == "Done":
        # Serve using context data from snapshot
        snapshots = meta.get_snapshots(session, interpretation.id)

        link_filter = {
            "annotation_id": [s.annotation_id for s in snapshots if s.annotation_id is not None],
            "customannotation_id": [
                s.customannotation_id for s in snapshots if s.customannotation_id is not None
            ],
            "alleleassessment_id": [
                s.alleleassessment_id for s in snapshots if s.alleleassessment_id is not None
            ],
            "allelereport_id": [
                s.allelereport_id for s in snapshots if s.allelereport_id is not None
            ],
        }

        # For historical referenceassessments, they should all be connected to the alleleassessments used
        ra_ids = (
            session.query(assessment.ReferenceAssessment.id)
            .join(assessment.AlleleAssessment.referenceassessments)
            .filter(assessment.AlleleAssessment.id.in_(link_filter["alleleassessment_id"]))
            .all()
        )
        link_filter["referenceassessment_id"] = [i[0] for i in ra_ids]

    # Only relevant for analysisinterpretation: Include the genotype for connected samples
    analysis_id = None
    if analysisinterpretation_id is not None:
        analysis_id = interpretation.analysis_id

    kwargs = {
        "include_annotation": True,
        "include_custom_annotation": True,
        "genepanel": interpretation.genepanel,
        "analysis_id": analysis_id,
        "link_filter": link_filter,
        "filterconfig_id": filterconfig_id,
    }

    return AlleleDataLoader(session).from_objs(alleles, **kwargs)


def load_genepanel_for_allele_ids(
    session: Session,
    allele_ids: Sequence[int],
    gp_name: str,
    gp_version: str,
):
    """
    Loads genepanel data using input allele_ids as filter
    for what transcripts and phenotypes to include.
    """
    genepanel = (
        session.query(gene.Genepanel)
        .filter(gene.Genepanel.name == gp_name, gene.Genepanel.version == gp_version)
        .one()
    )

    annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
        session, [(gp_name, gp_version)], allele_ids=allele_ids
    ).subquery()

    transcripts = (
        session.query(gene.Transcript)
        .options(joinedload(gene.Transcript.gene))
        .join(gene.Genepanel.transcripts)
        .filter(
            gene.Transcript.transcript_name
            == annotation_transcripts_genepanel.c.genepanel_transcript,
        )
        .all()
    )

    phenotypes = (
        session.query(gene.Phenotype)
        .options(joinedload(gene.Phenotype.gene))
        .join(gene.genepanel_phenotype)
        .filter(
            gene.Transcript.transcript_name
            == annotation_transcripts_genepanel.c.genepanel_transcript,
            gene.Phenotype.gene_id == gene.Transcript.gene_id,
            gene.genepanel_phenotype.c.genepanel_name == gp_name,
            gene.genepanel_phenotype.c.genepanel_version == gp_version,
        )
    )

    geneassessments = (
        session.query(assessment.GeneAssessment)
        .filter(
            assessment.GeneAssessment.gene_id
            == annotation_transcripts_genepanel.c.genepanel_hgnc_id,
            assessment.GeneAssessment.date_superceeded.is_(None),
        )
        .all()
    )

    genepanel_data = schemas.GenepanelSchema().dump(genepanel).data
    genepanel_data["transcripts"] = schemas.TranscriptFullSchema().dump(transcripts, many=True).data
    genepanel_data["phenotypes"] = schemas.PhenotypeFullSchema().dump(phenotypes, many=True).data
    genepanel_data["geneassessments"] = (
        schemas.GeneAssessmentSchema().dump(geneassessments, many=True).data
    )
    return genepanel_data


def update_interpretation(
    session: Session,
    user_id: dict,
    data: PatchInterpretationRequest,
    *,
    alleleinterpretation_id: int = None,
    analysisinterpretation_id: int = None,
):
    """
    Updates the current interpretation inplace.

    **Only allowed for interpretations that are `Ongoing`**

    """
    model_id, meta = _get_interpretation_meta(
        allele_id=alleleinterpretation_id, analysis_id=analysisinterpretation_id
    )
    interpretation = meta.get_interpretation(session, model_id)

    if interpretation.status == "Done":
        raise ConflictError("Cannot PATCH interpretation with status 'DONE'")
    elif interpretation.status == "Not started":
        raise ConflictError(
            "Interpretation not started. Call it's analysis' start action to begin interpretation."
        )

    # Check that user is same as before
    if interpretation.user_id:
        if interpretation.user_id != user_id:
            current_user = session.query(user.User).filter(user.User.id == user_id).one()
            interpretation_user = (
                session.query(user.User).filter(user.User.id == interpretation.user_id).one()
            )
            raise ConflictError(
                "Interpretation owned by {} {} cannot be updated by other user ({} {})".format(
                    interpretation_user.first_name,
                    interpretation.user.last_name,
                    current_user.first_name,
                    current_user.last_name,
                )
            )

    # Add current state to history if new state is different:
    if data.state != interpretation.state:
        session.add(
            workflow.InterpretationStateHistory(
                alleleinterpretation_id=alleleinterpretation_id,
                analysisinterpretation_id=analysisinterpretation_id,
                state=interpretation.state,
                user_id=user_id,
            )
        )
    # Overwrite state fields with new values
    interpretation.state = data.state
    interpretation.user_state = data.user_state
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)
    return interpretation


def get_interpretation(
    session: Session,
    genepanels: Sequence[gene.Genepanel],
    user_id: int,
    *,
    alleleinterpretation_id: int = None,
    analysisinterpretation_id: int = None,
):
    interpretation_id, meta = _get_interpretation_meta(
        allele_id=alleleinterpretation_id, analysis_id=analysisinterpretation_id
    )

    interpretation = meta.get_interpretation(session, interpretation_id, genepanels)
    obj = meta.schema().dump(interpretation).data
    return obj


def get_interpretations(
    session: Session,
    genepanels: Sequence[gene.Genepanel],
    user_id: int,
    *,
    allele_id: int = None,
    analysis_id: int = None,
    filterconfig_id: int = None,
):
    model_id, meta = _get_interpretation_meta(allele_id=allele_id, analysis_id=analysis_id)
    interpretations = meta.get_model_interpretations(session, model_id, genepanels)
    loaded_interpretations = []
    if interpretations:
        loaded_interpretations = meta.schema().dump(interpretations, many=True).data

    return loaded_interpretations


def override_interpretation(
    session: Session,
    user_id: int,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    model_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id,
        analysis_id=workflow_analysis_id,
    )

    interpretation = meta.get_latest_interpretation(session, model_id)

    # Get user by username
    new_user = session.query(user.User).filter(user.User.id == user_id).one()

    if interpretation.status != "Ongoing":
        raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = new_user
    return interpretation


def start_interpretation(
    session: Session,
    user_id: int,
    data: Optional[AlleleActionStartRequest],
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    model_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id, analysis_id=workflow_analysis_id
    )
    interpretation = meta.get_latest_interpretation(session, model_id)

    # Get user by username
    start_user = session.query(user.User).filter(user.User.id == user_id).one()

    if not interpretation:
        interpretation = meta.model()
        setattr(interpretation, meta.model_id.name, model_id)
        session.add(interpretation)
    elif interpretation.status != "Not started":
        raise ApiError(
            f"Cannot start existing interpretation where status = {interpretation.status}"
        )

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = start_user
    interpretation.status = "Ongoing"
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    if meta.name is WorkflowTypes.ANALYSIS:
        analysis = session.query(sample.Analysis).filter(sample.Analysis.id == model_id).one()
        interpretation.genepanel = analysis.genepanel
    elif meta.name is WorkflowTypes.ALLELE:
        if data is None:
            raise ValueError(f"Cannot create allele intepretation without genepanel info")
        # For allele workflow, the user can choose genepanel context for each interpretation
        interpretation.genepanel_name = data.gp_name
        interpretation.genepanel_version = data.gp_version
    else:
        # shouldn't have happen, but just in case
        raise RuntimeError("Missing id argument")

    return interpretation


def mark_interpretation(
    session: Session,
    workflow_status: str,
    data: _MarkInterpretationRequest,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    """
    Marks (and copies) an interpretation for a new workflow_status,
    creating Snapshot objects to record history.
    """
    model_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id,
        analysis_id=workflow_analysis_id,
    )
    interpretation = meta.get_latest_interpretation(session, model_id)
    assert interpretation is not None, f"No {meta.model.__name__} found for id {model_id}"

    if not interpretation.status == "Ongoing":
        raise ApiError(
            "Cannot mark as '{}' when latest interpretation is not 'Ongoing'".format(
                workflow_status
            )
        )

    excluded_allele_ids = None
    if type(data) is MarkAnalysisInterpretationRequest:
        excluded_allele_ids = data.excluded_allele_ids

    SnapshotCreator(session).insert_from_data(
        data.allele_ids,
        meta.name,
        interpretation,
        data.annotation_ids,
        data.custom_annotation_ids,
        data.alleleassessment_ids,
        data.allelereport_ids,
        excluded_allele_ids=excluded_allele_ids,
    )

    interpretation.status = "Done"
    interpretation.finalized = False
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    # Create next interpretation
    interpretation_next = meta.model.create_next(interpretation)
    interpretation_next.workflow_status = workflow_status
    session.add(interpretation_next)

    return interpretation, interpretation_next


def marknotready_interpretation(
    session: Session,
    data: _MarkInterpretationRequest,
    *,
    workflow_analysis_id: int = None,
):
    return mark_interpretation(
        session,
        "Not ready",
        data,
        workflow_analysis_id=workflow_analysis_id,
    )


def markinterpretation_interpretation(
    session: Session,
    data: _MarkInterpretationRequest,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    return mark_interpretation(
        session,
        "Interpretation",
        data,
        workflow_allele_id=workflow_allele_id,
        workflow_analysis_id=workflow_analysis_id,
    )


def markreview_interpretation(
    session: Session,
    data: _MarkInterpretationRequest,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    return mark_interpretation(
        session,
        "Review",
        data,
        workflow_allele_id=workflow_allele_id,
        workflow_analysis_id=workflow_analysis_id,
    )


def markmedicalreview_interpretation(
    session: Session,
    data: _MarkInterpretationRequest,
    *,
    workflow_analysis_id: int,
):
    return mark_interpretation(
        session,
        "Medical review",
        data,
        workflow_analysis_id=workflow_analysis_id,
    )


def reopen_interpretation(
    session: Session,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    model_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id,
        analysis_id=workflow_analysis_id,
    )
    interpretation = meta.get_latest_interpretation(session, model_id)

    if interpretation is None:
        raise ApiError(
            "There are no existing interpretations for this item. Use the start action instead."
        )

    if not interpretation.status == "Done":
        raise ApiError("Interpretation is already 'Not started' or 'Ongoing'. Cannot reopen.")

    # Create next interpretation
    interpretation_next = meta.model.create_next(interpretation)
    interpretation_next.workflow_status = (
        interpretation.workflow_status
    )  # TODO: Where do we want to go?
    session.add(interpretation_next)

    return interpretation, interpretation_next


def finalize_allele(
    session: Session,
    user_id: int,
    usergroup_id: int,
    data: FinalizeAlleleRequest,
    user_config: UserConfig,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    """
    Finalizes a single allele.

    This will create any [alleleassessment|referenceassessments|allelereport] objects for the provided allele id (in data).

    **Only works for workflows with a `Ongoing` current interpretation**
    """
    workflow_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id, analysis_id=workflow_analysis_id
    )
    interpretation = meta.get_latest_interpretation(session, workflow_id)

    if not interpretation.status == "Ongoing":
        raise ApiError("Cannot finalize allele when latest interpretation is not 'Ongoing'")

    if meta.name is WorkflowTypes.ALLELE:
        assert data.allele_id == workflow_allele_id
    elif meta.name is WorkflowTypes.ANALYSIS:
        assert (
            session.query(allele.Allele)
            .join(
                allele.Allele.genotypes,
                sample.Sample,
                sample.Analysis,
            )
            .filter(
                sample.Analysis.id == workflow_analysis_id,
                allele.Allele.id == data.allele_id,
            )
            .distinct()
            .count()
            == 1
        )

    # Check annotation data
    latest_annotation_id: int = (
        session.query(annotation.Annotation.id)
        .filter(
            annotation.Annotation.allele_id == data.allele_id,
            annotation.Annotation.date_superceeded.is_(None),
        )
        .scalar()
    )
    if latest_annotation_id != data.annotation_id:
        raise ApiError(
            "Cannot finalize: provided annotation_id does not match latest annotation id"
        )

    latest_customannotation_id: Optional[int] = (
        session.query(annotation.CustomAnnotation.id)
        .filter(
            annotation.CustomAnnotation.allele_id == data.allele_id,
            annotation.CustomAnnotation.date_superceeded.is_(None),
        )
        .scalar()
    )
    if latest_customannotation_id != data.custom_annotation_id:
        raise ApiError(
            "Cannot finalize: provided custom_annotation_id does not match latest annotation id"
        )

    # Create/reuse assessments
    assessment_result = AssessmentCreator(session).create_from_data(
        user_id,
        usergroup_id,
        data.allele_id,
        data.annotation_id,
        data.custom_annotation_id,
        interpretation.genepanel_name,
        interpretation.genepanel_version,
        data.alleleassessment.dump(),
        [ra.dump() for ra in data.referenceassessments],
        analysis_id=workflow_analysis_id,
    )

    if assessment_result.created_alleleassessment or assessment_result.created_referenceassessments:
        # Check that we can finalize allele
        finalize_requirements: Union[
            AlleleFinalizeRequirementsConfig, AnalysisFinalizeRequirementsConfig
        ]
        if meta.name is WorkflowTypes.ALLELE:
            finalize_requirements = _get_finalize_reqs(user_config, meta.name)
        elif meta.name is WorkflowTypes.ANALYSIS:
            finalize_requirements = _get_finalize_reqs(user_config, meta.name)
        else:
            raise ValueError(f"Invalid workflow type: {meta.name}")

        if (
            finalize_requirements.workflow_status
            and interpretation.workflow_status not in finalize_requirements.workflow_status
        ):
            raise ApiError(
                "Cannot finalize: interpretation workflow status is {}, but must be one of: {}".format(
                    interpretation.workflow_status,
                    ", ".join(finalize_requirements.workflow_status),
                )
            )

    alleleassessment = None
    if assessment_result.created_alleleassessment:
        session.add(assessment_result.created_alleleassessment)
    else:
        if assessment_result.created_referenceassessments:
            raise ApiError(
                "Trying to create referenceassessments for allele, while not also creating alleleassessment"
            )

    if assessment_result.created_referenceassessments:
        session.add_all(assessment_result.created_referenceassessments)

    # Create/reuse allelereports
    report_result = AlleleReportCreator(session).create_from_data(
        user_id,
        usergroup_id,
        data.allele_id,
        data.allelereport.dump(),
        alleleassessment,
        analysis_id=workflow_analysis_id,
    )

    if report_result.created_allelereport:
        # Do not check if finalize is allowed, report updates are always allowed
        session.add(report_result.created_allelereport)

    session.flush()

    # Ensure that we created either alleleassessment or allelereport, otherwise finalization
    # makes no sense.
    assert assessment_result.created_alleleassessment or report_result.created_allelereport

    # Create entry in interpretation log
    il_data = {"user_id": user_id, meta.snapshot_id.name: interpretation.id}
    if assessment_result.created_alleleassessment:
        il_data["alleleassessment_id"] = assessment_result.created_alleleassessment.id
    if report_result.created_allelereport:
        il_data["allelereport_id"] = report_result.created_allelereport.id

    il = workflow.InterpretationLog(**il_data)
    session.add(il)

    return {
        "allelereport": schemas.AlleleReportSchema().dump(report_result.allelereport).data,
        "alleleassessment": schemas.AlleleAssessmentSchema()
        .dump(assessment_result.alleleassessment)
        .data,
        "referenceassessments": schemas.ReferenceAssessmentSchema()
        .dump(assessment_result.referenceassessments, many=True)
        .data,
    }


def finalize_workflow(
    session: Session,
    user_id: int,
    data: _MarkInterpretationRequest,
    user_config: UserConfig,
    *,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    """
    Finalizes an interpretation.

    This sets the allele/analysis' current interpretation's status to `Done`,
    and finalized to True.

    The provided data is recorded in a snapshot to be able to present user
    with the view at end of interpretation round.

    **Only works for analyses with a `Ongoing` current interpretation**
    """
    workflow_id, meta = _get_interpretation_meta(
        allele_id=workflow_allele_id,
        analysis_id=workflow_analysis_id,
    )
    interpretation = meta.get_latest_interpretation(session, workflow_id)

    if interpretation is None:
        raise ApiError(f"No interpretation found for {meta.name} id {workflow_id}")
    elif interpretation.status != "Ongoing":
        raise ApiError("Cannot finalize when latest interpretation is not 'Ongoing'")

    # Sanity checks
    alleleassessment_allele_ids = set(
        session.query(assessment.AlleleAssessment.allele_id)
        .filter(assessment.AlleleAssessment.id.in_(data.alleleassessment_ids))
        .scalar_all()
    )

    allelereport_allele_ids: Set[int] = set(
        session.query(assessment.AlleleReport.allele_id)
        .filter(assessment.AlleleReport.id.in_(data.allelereport_ids))
        .scalar_all()
    )

    assert alleleassessment_allele_ids - set(data.allele_ids) == set()
    assert allelereport_allele_ids - set(data.allele_ids) == set()

    # Check that we can finalize
    # There are different criterias deciding when finalization is allowed
    finalize_requirements: Union[
        AlleleFinalizeRequirementsConfig, AnalysisFinalizeRequirementsConfig
    ]
    if meta.name is WorkflowTypes.ALLELE:
        assert type(data) is MarkAlleleInterpretationRequest
        finalize_requirements = _get_finalize_reqs(user_config, meta.name)
        excluded_allele_ids = None
    elif meta.name is WorkflowTypes.ANALYSIS:
        assert type(data) is MarkAnalysisInterpretationRequest
        finalize_requirements = _get_finalize_reqs(user_config, meta.name)
        excluded_allele_ids = data.excluded_allele_ids

        if finalize_requirements.allow_technical is False and data.technical_allele_ids:
            raise ApiError(
                "allow_technical is set to false, but some allele ids are marked technical"
            )

        if finalize_requirements.allow_notrelevant is False and data.notrelevant_allele_ids:
            raise ApiError(
                "allow_notrelevant is set to false, but some allele ids are marked not relevant"
            )

        unclassified_allele_ids = (
            set(data.allele_ids)
            - set(data.notrelevant_allele_ids)
            - set(data.technical_allele_ids)
            - alleleassessment_allele_ids
        )
        if finalize_requirements.allow_unclassified is False and unclassified_allele_ids:
            raise ApiError(
                "allow_unclassified is set to false, but some allele ids are missing classification"
            )
    else:
        raise ValueError(f"Invalid workflow: {meta.name}")

    if (
        finalize_requirements.workflow_status is not None
        and interpretation.workflow_status not in [s for s in finalize_requirements.workflow_status]
    ):
        raise ApiError(
            "Cannot finalize: interpretation workflow status is {}, but must be one of: {}".format(
                interpretation.workflow_status,
                ", ".join(finalize_requirements.workflow_status),
            )
        )

    # Create interpretation snapshot objects
    SnapshotCreator(session).insert_from_data(
        data.allele_ids,
        meta.name,
        interpretation,
        data.annotation_ids,
        data.custom_annotation_ids,
        data.alleleassessment_ids,
        data.allelereport_ids,
        excluded_allele_ids=excluded_allele_ids,
    )

    # Update interpretation
    interpretation.status = "Done"
    interpretation.finalized = True
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)


def get_genepanels(session: Session, allele_ids: Sequence[int], user: Optional[user.User] = None):
    """
    Get all genepanels overlapping the regions of the provided allele_ids.

    Is user is provided, the genepanels are restricted to the user group's panels.
    """
    if user:
        # TODO: This can turn into a perforamance issue
        gp_keys = sorted([(g.name, g.version) for g in user.group.genepanels if g.official])
    else:
        gp_keys = (
            session.query(gene.Genepanel.name, gene.Genepanel.version)
            .filter(gene.Genepanel.official.is_(True))
            .all()
        )

    allele_genepanels = queries.allele_genepanels(session, gp_keys, allele_ids=allele_ids)
    allele_genepanels = allele_genepanels.subquery()
    candidate_genepanels = (
        session.query(
            allele_genepanels.c.name, allele_genepanels.c.version, allele_genepanels.c.official
        )
        .distinct()
        .all()
    )

    # TODO: Sort by previously used interpretations

    result = schemas.GenepanelSchema().dump(candidate_genepanels, many=True)
    return result


def get_workflow_allele_collisions(
    session: Session,
    allele_ids: Sequence[int],
    *,
    analysis_id: int = None,
    allele_id: int = None,
):
    """
    Check for possible collisions in other allele or analysis workflows,
    which happens to have overlapping alleles with the ids given in 'allele_ids'.

    If you're checking a specific workflow, include the analysis_id or allele_id argument
    to specify which workflow to exclude from the check.
    For instance, if you want to check analysis 3, having e.g. 20 alleles, you don't want
    to include analysis 3 in the collision check as it's not informative
    to see a collision with itself. You would pass in analysis_id=3 to exclude it.

    :note: Alleles with valid alleleassessments are excluded from causing collision.
    """
    workflow_analysis_ids = _get_uncommitted_interpretation_ids(session, AnalysisInterpretationMeta)

    # Exclude "ourself" if applicable
    if analysis_id in workflow_analysis_ids:
        workflow_analysis_ids.remove(analysis_id)

    ongoing: Dict[WorkflowTypes, List[OngoingWorkflow]] = {}
    # Get all ongoing analyses connected to provided allele ids
    # For analyses we exclude alleles with valid alleleassessments
    ongoing[WorkflowTypes.ANALYSIS] = [
        OngoingWorkflow.from_orm(row)  # type: ignore
        for row in session.query(
            workflow.AnalysisInterpretation.user_id,
            workflow.AnalysisInterpretation.workflow_status,
            allele.Allele.id.label("allele_id"),
            workflow.AnalysisInterpretation.analysis_id,
        )
        .join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            workflow.AnalysisInterpretation,
        )
        .filter(
            sample.Analysis.id.in_(workflow_analysis_ids),
            allele.Allele.id.in_(allele_ids),
            ~allele.Allele.id.in_(queries.allele_ids_with_valid_alleleassessments(session)),
        )
        .distinct(workflow.AnalysisInterpretation.analysis_id, allele.Allele.id)
        .order_by(
            workflow.AnalysisInterpretation.analysis_id,
            allele.Allele.id,
            workflow.AnalysisInterpretation.date_created.desc(),
        )
        .all()
    ]

    # Allele workflow
    workflow_allele_ids = _get_uncommitted_interpretation_ids(session, AlleleInterpretationMeta)

    # Exclude "ourself" if applicable
    if allele_id in workflow_allele_ids:
        workflow_allele_ids.remove(allele_id)

    ongoing[WorkflowTypes.ALLELE] = [
        OngoingWorkflow.from_orm(row)  # type: ignore
        for row in session.query(
            workflow.AlleleInterpretation.user_id,
            workflow.AlleleInterpretation.workflow_status,
            workflow.AlleleInterpretation.allele_id,
            literal(None).label("analysis_id"),
        )
        .filter(
            workflow.AlleleInterpretation.allele_id.in_(workflow_allele_ids),
            workflow.AlleleInterpretation.allele_id.in_(allele_ids),
        )
        .distinct(workflow.AlleleInterpretation.allele_id)
        .order_by(
            workflow.AlleleInterpretation.allele_id,
            workflow.AlleleInterpretation.date_created.desc(),
        )
        .all()
    ]

    # Preload users, analysis names
    user_ids: Set[int] = set()
    analysis_ids: List[int] = []
    for wf_type in ongoing:
        for wf in ongoing[wf_type]:
            if wf.user_id is not None:
                user_ids.add(wf.user_id)
            if wf_type is WorkflowTypes.ANALYSIS and wf.analysis_id:
                analysis_ids.append(wf.analysis_id)
    user_map: Dict[int, Dict[str, Any]] = {
        u["id"]: u
        for u in schemas.UserSchema()
        .dump(
            session.query(user.User).filter(user.User.id.in_(user_ids)).all(),
            many=True,
        )
        .data
    }

    # Preload the analysis names
    analysis_name_by_id = {
        row.id: row.name
        for row in session.query(sample.Analysis.id, sample.Analysis.name)
        .filter(sample.Analysis.id.in_(analysis_ids))
        .all()
    }

    collisions: List[AlleleCollision] = list()
    for wf_type, wf_entries in ongoing.items():
        for wf_obj in wf_entries:
            # If a workflow is in review, it will have no user assigned...
            collisions.append(
                AlleleCollision.parse_obj(
                    {
                        **wf_obj.dump(exclude_none=True, exclude={"user_id"}),
                        "type": wf_type,
                        "user": None if wf_obj.user_id is None else user_map.get(wf_obj.user_id),
                        "analysis_name": analysis_name_by_id.get(wf_obj.analysis_id),
                    }
                )
            )

    return collisions


def get_interpretationlog(
    session: Session, user_id: int, *, allele_id: int = None, analysis_id: int = None
):
    workflow_id, meta = _get_interpretation_meta(allele_id=allele_id, analysis_id=analysis_id)

    latest_interpretation = meta.get_latest_interpretation(session, workflow_id)
    # If there's no interpretations, there cannot be any logs either
    if latest_interpretation is None:
        return {"logs": [], "users": []}

    logs = (
        session.query(workflow.InterpretationLog)
        .join(meta.model)
        .filter(meta.model_id == workflow_id)
        .order_by(workflow.InterpretationLog.date_created)
    )

    id_field = "alleleinterpretation_id" if allele_id else "analysisinterpretation_id"
    editable = {
        l.id: getattr(l, id_field) == latest_interpretation.id
        and (not latest_interpretation.finalized or latest_interpretation.status != "Done")
        and l.user_id == user_id
        and l.message is not None
        for l in logs
    }
    loaded_logs: List[Dict] = schemas.InterpretationLogSchema().dump(logs, many=True).data

    for loaded_log in loaded_logs:
        loaded_log["editable"] = editable[loaded_log["id"]]

    # AlleleAssessments and AlleleReports are special, we need to load more data
    alleleassessment_ids: Set[int] = set(
        [l["alleleassessment_id"] for l in loaded_logs if l["alleleassessment_id"]]
    )
    alleleassessments: List[assessment.AlleleAssessment] = (
        session.query(
            assessment.AlleleAssessment.id,
            assessment.AlleleAssessment.allele_id,
            assessment.AlleleAssessment.classification,
            assessment.AlleleAssessment.previous_assessment_id,
        )
        .filter(assessment.AlleleAssessment.id.in_(alleleassessment_ids))
        .all()
    )
    alleleassessments_by_id = {a.id: a for a in alleleassessments}

    previous_assessment_ids = [
        a.previous_assessment_id for a in alleleassessments if a.previous_assessment_id
    ]
    previous_alleleassessment_classifications: List[assessment.AlleleAssessment] = (
        session.query(assessment.AlleleAssessment.id, assessment.AlleleAssessment.classification)
        .filter(assessment.AlleleAssessment.id.in_(previous_assessment_ids))
        .all()
    )
    previous_alleleassessment_classifications_by_id = {
        a.id: a.classification for a in previous_alleleassessment_classifications
    }

    allele_ids = [a.allele_id for a in alleleassessments]

    allelereport_ids = set([l["allelereport_id"] for l in loaded_logs if l["allelereport_id"]])
    allelereports = (
        session.query(assessment.AlleleReport.id, assessment.AlleleReport.allele_id)
        .filter(assessment.AlleleReport.id.in_(allelereport_ids))
        .all()
    )
    allelereports_by_id = {a.id: a for a in allelereports}

    allele_ids.extend([a.allele_id for a in allelereports])
    annotation_genepanel = queries.annotation_transcripts_genepanel(
        session,
        [(latest_interpretation.genepanel_name, latest_interpretation.genepanel_version)],
        allele_ids=allele_ids,
    ).subquery()

    allele_hgvs = (
        session.query(
            allele.Allele.id,
            allele.Allele.chromosome,
            allele.Allele.vcf_pos,
            allele.Allele.vcf_ref,
            allele.Allele.vcf_alt,
            annotation_genepanel.c.annotation_symbol,
            annotation_genepanel.c.annotation_hgvsc,
        )
        .outerjoin(annotation_genepanel, annotation_genepanel.c.allele_id == allele.Allele.id)
        .filter(allele.Allele.id.in_(allele_ids))
        .all()
    )

    formatted_allele_by_id: DefaultDict[int, List] = defaultdict(list)
    for a in allele_hgvs:
        if a.annotation_hgvsc:
            formatted_allele_by_id[a.id].append(f"{a.annotation_symbol} {a.annotation_hgvsc}")
        else:
            formatted_allele_by_id[a.id].append(
                f"{a.chromosome}:{a.vcf_pos} {a.vcf_ref}>{a.vcf_alt}"
            )

    for loaded_log in loaded_logs:
        alleleassessment_id = loaded_log.pop("alleleassessment_id", None)
        if alleleassessment_id:
            log_aa = alleleassessments_by_id[alleleassessment_id]
            loaded_log["alleleassessment"] = {
                "allele_id": log_aa.allele_id,
                "hgvsc": sorted(formatted_allele_by_id[log_aa.allele_id]),
                "classification": log_aa.classification,
                "previous_classification": previous_alleleassessment_classifications_by_id[
                    log_aa.previous_assessment_id
                ]
                if log_aa.previous_assessment_id
                else None,
            }

        allelereport_id = loaded_log.pop("allelereport_id", None)
        if allelereport_id:
            log_ar = allelereports_by_id[allelereport_id]
            loaded_log["allelereport"] = {
                "allele_id": log_ar.allele_id,
                "hgvsc": sorted(formatted_allele_by_id[log_ar.allele_id]),
            }

    # Load all relevant user data
    user_ids = set([l["user_id"] for l in loaded_logs])
    users = session.query(user.User).filter(user.User.id.in_(user_ids)).all()

    loaded_users = schemas.UserSchema().dump(users, many=True).data

    return {"logs": loaded_logs, "users": loaded_users}


def create_interpretationlog(
    session: Session,
    user_id: int,
    data: CreateInterpretationLogRequest,
    *,
    allele_id: int = None,
    analysis_id: int = None,
):
    model_id, meta = _get_interpretation_meta(allele_id=allele_id, analysis_id=analysis_id)
    if meta.name is WorkflowTypes.ALLELE and data.warning_cleared is not None:
        raise ApiError("warning_cleared is not supported for alleles as they have no warnings")

    latest_interpretation = meta.get_latest_interpretation(session, model_id)

    if not latest_interpretation:
        # Shouldn't be possible for an analysis
        assert (
            meta.name is WorkflowTypes.ALLELE
        ), f"Failed to find latest interpretation for analysis {model_id}"

        latest_interpretation = workflow.AlleleInterpretation(
            allele_id=allele_id,
            workflow_status="Interpretation",
            status="Not started",
        )
        session.add(latest_interpretation)
        session.flush()

    new_log = data.dict()
    new_log[meta.snapshot_id_field] = latest_interpretation.id
    new_log["user_id"] = user_id

    il = workflow.InterpretationLog(**new_log)

    session.add(il)
    return il


def patch_interpretationlog(
    session: Session,
    user_id: int,
    interpretationlog_id: int,
    message: str,
    *,
    allele_id: int = None,
    analysis_id: int = None,
):
    il = (
        session.query(workflow.InterpretationLog)
        .filter(workflow.InterpretationLog.id == interpretationlog_id)
        .one()
    )

    if il.user_id != user_id:
        raise ApiError("Cannot edit interpretation log, item doesn't match user's id.")

    model_id, meta = _get_interpretation_meta(allele_id=allele_id, analysis_id=analysis_id)
    latest_interpretation = meta.get_latest_interpretation(session, model_id)

    match = False
    if meta.name is WorkflowTypes.ALLELE:
        match = il.alleleinterpretation_id == latest_interpretation.id
    elif meta.name is WorkflowTypes.ANALYSIS:
        match = il.analysisinterpretation_id == latest_interpretation.id

    if not match:
        raise ApiError("Can only edit entries created for latest interpretation id.")

    il.message = message


def delete_interpretationlog(
    session: Session,
    user_id: int,
    interpretationlog_id: int,
    *,
    allele_id: int = None,
    analysis_id: int = None,
):
    il = (
        session.query(workflow.InterpretationLog)
        .filter(workflow.InterpretationLog.id == interpretationlog_id)
        .one()
    )

    if il.user_id != user_id:
        raise ApiError("Cannot delete interpretation log, item doesn't match user's id.")

    model_id, meta = _get_interpretation_meta(allele_id=allele_id, analysis_id=analysis_id)
    latest_interpretation = meta.get_latest_interpretation(session, model_id)

    match = False
    if meta.name is WorkflowTypes.ALLELE:
        match = il.alleleinterpretation_id == latest_interpretation.id
    elif meta.name is WorkflowTypes.ANALYSIS:
        match = il.analysisinterpretation_id == latest_interpretation.id

    if not match:
        raise ApiError("Can only delete entries created for latest interpretation id.")

    session.delete(il)


"""
returns
    {
        "cnv": [1,2,3,4],
        "snv": [5,6]
    }
"""


def fetch_allele_ids_by_caller_type(session: Session, excluded_alleles: Sequence[int]):
    return dict(
        session.query(allele.Allele.caller_type, func.array_agg(allele.Allele.id))
        .filter(and_(allele.Allele.id.in_(excluded_alleles)))
        .group_by(allele.Allele.caller_type)
        .all()
    )


def filtered_by_caller_type(session: Session, filtered_alleles: Dict[str, List[int]]):
    # concatenates all the ids of each
    flattened_ids: List[int] = sum(filtered_alleles.values(), [])
    alleles_by_caller_type = fetch_allele_ids_by_caller_type(session, flattened_ids)
    filtered_by_caller_type: Dict[CallerTypes, Dict[str, List[int]]] = {c: {} for c in CallerTypes}
    for caller_type in filtered_by_caller_type:
        for filter_type in filtered_alleles:
            ids = filtered_alleles[filter_type]
            if len(ids) == 0:
                filtered_by_caller_type[caller_type][filter_type] = []
            else:
                if caller_type in alleles_by_caller_type:
                    active_alleles = alleles_by_caller_type[caller_type]
                    filtered_by_caller_type[caller_type][filter_type] = list(
                        set(active_alleles) & set(ids)
                    )
                else:
                    filtered_by_caller_type[caller_type][filter_type] = []
    return filtered_by_caller_type


# Revert to old way
def get_filtered_alleles(
    session: Session, interpretation: _Interp, filter_config_id: int = None
) -> Tuple[List[int], Optional[Dict[str, List[int]]]]:
    """
    Return filter results for interpretation.
    - If AlleleInterpretation, return only allele id for interpretation (no alleles excluded)
    - If AnalysisInterpretation:
        - filter_config_id not provided: Return snapshot results. Requires interpretation to be 'Done'-
        - filter_config_id provided: Run filter on analysis, and return results.
    """
    if isinstance(interpretation, workflow.AlleleInterpretation):
        return [interpretation.allele_id], None
    elif isinstance(interpretation, workflow.AnalysisInterpretation):
        if filter_config_id is None:
            if interpretation.status != "Done":
                raise RuntimeError("Interpretation is not done, and no filter config is provided.")

            if not interpretation.snapshots:
                # snapshots will be empty if there are no variants
                has_alleles = any(
                    [s.genotypes for s in interpretation.analysis.samples if s.proband]
                )

                if has_alleles:
                    raise RuntimeError("Missing snapshots for interpretation.")

            allele_ids: List[int] = []
            excluded_allele_ids: Dict[str, List[int]] = {
                k.value: [] for k in FilteredAlleleCategories
            }

            for snapshot in interpretation.snapshots:
                if snapshot.filtered in FilteredAlleleCategories.__members__:
                    excluded_allele_ids[str(FilteredAlleleCategories[snapshot.filtered])].append(
                        snapshot.allele_id
                    )
                else:
                    allele_ids.append(snapshot.allele_id)

            return allele_ids, excluded_allele_ids
        else:
            analysis_id = interpretation.analysis_id
            analysis_allele_ids: List[int] = (
                session.query(allele.Allele.id)
                .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
                .filter(sample.Analysis.id == analysis_id)
                .scalar_all()
            )

            af = AlleleFilter(session)
            filtered_alleles = af.filter_analysis(
                filter_config_id,
                analysis_id,
                analysis_allele_ids,
            )

            return filtered_alleles["allele_ids"], filtered_alleles["excluded_allele_ids"]
    else:
        raise RuntimeError(f"Unknown interpretation type {interpretation}")


@overload
def _get_finalize_reqs(
    cfg: UserConfig, wf_type: Literal[WorkflowTypes.ALLELE]
) -> AlleleFinalizeRequirementsConfig:
    ...


@overload
def _get_finalize_reqs(
    cfg: UserConfig, wf_type: Literal[WorkflowTypes.ANALYSIS]
) -> AnalysisFinalizeRequirementsConfig:
    ...


def _get_finalize_reqs(cfg, wf_type):
    if not cfg.workflows:
        raise ValueError(f"User config missing: workflows")
    elif wf_type is WorkflowTypes.ALLELE:
        if not cfg.workflows.allele:
            raise ValueError(f"User config missing: workflows.allele")
        return cfg.workflows.allele.finalize_requirements
    elif wf_type is WorkflowTypes.ANALYSIS:
        if not cfg.workflows.analysis:
            raise ValueError(f"User config missing: workflows.analysis")
        return cfg.workflows.analysis.finalize_requirements
