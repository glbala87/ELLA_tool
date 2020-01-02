import angular from 'angular'
import { getReferencesIdsForAllele, findReferencesFromIds } from './reference'

export function compareAlleleReport(alleleState, allele) {
    // Whether allelereport has changed in state compared to original
    return (
        alleleState.allelereport &&
        allele.allele_report &&
        angular.toJson(alleleState.allelereport.evaluation) ==
            angular.toJson(allele.allele_report.evaluation)
    )
}

export function prepareInterpretationPayload(type, state, alleles, alleleIds, excludedAlleleIds) {
    // Collect info about this interpretation.
    const annotation_ids = []
    const custom_annotation_ids = []
    const alleleassessment_ids = []
    const allelereport_ids = []
    const technical_allele_ids = []
    const notrelevant_allele_ids = []

    // Collect presented data for snapshotting
    // and data needed for verification in backend
    for (let alleleState of Object.values(state.allele)) {
        if (!alleleState.allele_id) {
            throw Error('Missing mandatory property allele_id in allele state', alleleState)
        }
        if (alleleState.allele_id in alleles) {
            let allele = alleles[alleleState.allele_id]
            annotation_ids.push(allele.annotation.annotation_id)
            if (allele.annotation.custom_annotation_id) {
                custom_annotation_ids.push(allele.annotation.custom_annotation_id)
            }
            if (allele.allele_assessment) {
                alleleassessment_ids.push(allele.allele_assessment.id)
            }
            if (allele.allele_report) {
                allelereport_ids.push(allele.allele_report.id)
            }
            if (alleleState.analysis.verification === 'technical') {
                technical_allele_ids.push(alleleState.allele_id)
            }
            if (alleleState.analysis.notrelevant) {
                notrelevant_allele_ids.push(alleleState.allele_id)
            }
        }
    }

    const payload = {
        annotation_ids,
        custom_annotation_ids,
        alleleassessment_ids,
        allelereport_ids,
        allele_ids: alleleIds
    }
    if (type === 'analysis') {
        Object.assign(payload, {
            technical_allele_ids,
            notrelevant_allele_ids,
            excluded_allele_ids: excludedAlleleIds
        })
    }
    return payload
}

export function prepareAlleleFinalizePayload(allele, alleleState, references) {
    if (
        !alleleState.alleleassessment ||
        !(alleleState.alleleassessment.classification || alleleState.alleleassessment.reuse)
    ) {
        throw Error('Cannot finalize allele, no valid alleleassessment')
    }

    const payload = {
        allele_id: allele.id,
        annotation_id: allele.annotation.annotation_id,
        custom_annotation_id: allele.annotation.custom_annotation_id || null
    }

    payload.alleleassessment = _prepareAlleleAssessmentPayload(allele, alleleState)

    // Allele report is submitted independently of alleleassessment
    payload.allelereport = _prepareAlleleReportPayload(
        allele,
        alleleState,
        allele.allele_assessment ? allele.allele_assessment.id : null
    )

    // Get reference ids for allele, we only submit referenceassessments
    // belonging to this allele
    const alleleReferences = _getAlleleReferences(allele, references)
    payload.referenceassessments = _prepareReferenceAssessmentsPayload(
        alleleState,
        alleleReferences
    )

    return payload
}

function _getAlleleReferences(allele, references) {
    const alleleReferenceIds = getReferencesIdsForAllele(allele)
    return findReferencesFromIds(references, alleleReferenceIds).references
}

function _prepareAlleleAssessmentPayload(allele, allelestate) {
    const assessment_data = {
        allele_id: allele.id
    }

    if (allele.allele_assessment) {
        assessment_data.presented_alleleassessment_id = allele.allele_assessment.id
    }

    if (allelestate.alleleassessment.reuse) {
        assessment_data.reuse = true
    } else {
        Object.assign(assessment_data, {
            reuse: false,
            classification: allelestate.alleleassessment.classification,
            evaluation: allelestate.alleleassessment.evaluation,
            attachment_ids: allelestate.alleleassessment.attachment_ids
        })
    }
    return assessment_data
}

function _prepareReferenceAssessmentsPayload(allelestate, references) {
    let referenceassessments_data = []
    if ('referenceassessments' in allelestate) {
        // Iterate over all referenceassessments for this allele
        for (let referenceState of allelestate.referenceassessments) {
            // If not present among references, skip it
            if (!references.find((r) => r.id === referenceState.reference_id)) {
                continue
            }

            let ra = {
                reference_id: referenceState.reference_id,
                allele_id: referenceState.allele_id
            }

            // If id is included, we're reusing an existing one.
            if ('id' in referenceState) {
                ra.id = referenceState.id
            } else {
                // Fill in fields expected by backend
                ra.evaluation = referenceState.evaluation || {}
            }
            referenceassessments_data.push(ra)
        }
    }
    return referenceassessments_data
}

function _prepareAlleleReportPayload(allele, alleleState) {
    let report_data = {
        allele_id: allele.id
    }

    if (allele.allele_report) {
        report_data.presented_allelereport_id = allele.allele_report.id
    }

    // possible reuse:
    if (compareAlleleReport(alleleState, allele)) {
        report_data.reuse = true
    } else {
        report_data.reuse = false

        Object.assign(report_data, {
            evaluation: alleleState.allelereport.evaluation
        })
    }
    return report_data
}
