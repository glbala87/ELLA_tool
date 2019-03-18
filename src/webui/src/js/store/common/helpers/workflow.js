import angular from 'angular'
import { getReferencesIdsForAllele, findReferencesFromIds } from './reference'

export function prepareInterpretationPayload(
    type,
    id,
    interpretation,
    state,
    alleles,
    alleleIds,
    excludedAlleleIds,
    references
) {
    // Collect info about this interpretation.
    let annotations = []
    let custom_annotations = []
    let alleleassessments = []
    let referenceassessments = []
    let allelereports = []
    let attachments = []
    let technical_allele_ids = []
    let notrelevant_allele_ids = []

    // collection annotation ids for the alleles:
    for (let allele_state of Object.values(state.allele)) {
        if (!allele_state.allele_id) {
            throw Error('Missing mandatory property allele_id in allele state', allele_state)
        }
        if (allele_state.allele_id in alleles) {
            let allele = alleles[allele_state.allele_id]
            annotations.push({
                allele_id: allele.id,
                annotation_id: allele.annotation.annotation_id
            })
            if (allele.annotation.custom_annotation_id) {
                custom_annotations.push({
                    allele_id: allele.id,
                    custom_annotation_id: allele.annotation.custom_annotation_id
                })
            }
        }
    }

    for (let allele_state of Object.values(state.allele)) {
        // Only include assessments/reports for alleles part of the supplied list.
        // This is to avoid submitting assessments for alleles that have been
        // removed from classification during interpretation process.

        if (allele_state.allele_id in alleles) {
            let allele = alleles[allele_state.allele_id]
            // Only submit alleleassessment/allelereports/referenceassessments
            // for alleles that are classified
            if (
                allele_state.alleleassessment &&
                (allele_state.alleleassessment.classification ||
                    allele_state.alleleassessment.reuse)
            ) {
                alleleassessments.push(
                    _prepareAlleleAssessmentsPayload(
                        allele,
                        allele_state,
                        type === 'analysis' ? id : null,
                        interpretation.genepanel_name,
                        interpretation.genepanel_version
                    )
                )

                if (!allele_state.alleleassessment.reuse) {
                    attachments.push({
                        allele_id: allele_state.allele_id,
                        attachment_ids: allele_state.alleleassessment.attachment_ids
                    })
                }

                // Allele reports are submitted independently of alleleassessments
                allelereports.push(
                    _prepareAlleleReportPayload(
                        allele,
                        allele_state,
                        type === 'analysis' ? id : null,
                        allele.allele_assessment ? allele.allele_assessment.id : null
                    )
                )

                // Get reference ids from allele, we only submit referenceassessments
                // for references that are added (custom annotation or annotation)
                const alleleReferences = _getAlleleReferences(allele, references)
                referenceassessments = referenceassessments.concat(
                    _prepareReferenceAssessmentsPayload(
                        allele_state,
                        alleleReferences,
                        type === 'analysis' ? id : null,
                        interpretation.genepanel_name,
                        interpretation.genepanel_version
                    )
                )
            }

            if (allele_state.analysis.verification === 'technical') {
                technical_allele_ids.push(allele_state.allele_id)
            }

            if (allele_state.analysis.notrelevant) {
                notrelevant_allele_ids.push(allele_state.allele_id)
            }
        }
    }

    const payload = {
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments,
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

function _getAlleleReferences(allele, references) {
    const alleleReferenceIds = getReferencesIdsForAllele(allele)
    return findReferencesFromIds(references, alleleReferenceIds).references
}

function _prepareAlleleAssessmentsPayload(
    allele,
    allelestate,
    analysis_id = null,
    genepanel_name = null,
    genepanel_version = null
) {
    let assessment_data = {
        allele_id: allele.id
    }
    if (analysis_id) {
        assessment_data.analysis_id = analysis_id
    }
    if (genepanel_name && genepanel_version) {
        assessment_data.genepanel_name = genepanel_name
        assessment_data.genepanel_version = genepanel_version
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
            evaluation: allelestate.alleleassessment.evaluation
        })
    }
    return assessment_data
}

function _prepareReferenceAssessmentsPayload(
    allelestate,
    references,
    analysis_id = null,
    genepanel_name = null,
    genepanel_version = null
) {
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

            if (analysis_id) {
                ra.analysis_id = analysis_id
            }
            if (genepanel_name && genepanel_version) {
                ra.genepanel_name = genepanel_name
                ra.genepanel_version = genepanel_version
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

function _prepareAlleleReportPayload(
    allele,
    allelestate,
    analysis_id = null,
    alleleassessment_id = null
) {
    let report_data = {
        allele_id: allele.id
    }
    if (analysis_id) {
        report_data.analysis_id = analysis_id
    }
    if (alleleassessment_id) {
        report_data.alleleassessment_id = alleleassessment_id
    }

    if (allele.allele_report) {
        report_data.presented_allelereport_id = allele.allele_report.id
    }

    // possible reuse:
    if (
        allelestate.allelereport &&
        allele.allele_report &&
        angular.toJson(allelestate.allelereport.evaluation) ==
            angular.toJson(allele.allele_report.evaluation)
    ) {
        report_data.reuse = true
    } else {
        report_data.reuse = false
        // Fill in fields expected by backend
        Object.assign(report_data, {
            evaluation: allelestate.allelereport.evaluation
        })
    }
    return report_data
}
