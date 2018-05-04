import { deepCopy } from '../../../util'

function checkAlleleAssessmentModel(alleleState) {
    let alleleassesment = alleleState.alleleassessment

    if (!('attachment_ids' in alleleassesment)) {
        alleleassesment.attachment_ids = []
    }

    if (!('reuse' in alleleassesment)) {
        alleleassesment.reuse = false
    }

    if (!('classification' in alleleassesment)) {
        alleleassesment.classification = null
    }

    if (!('evaluation' in alleleassesment)) {
        alleleassesment.evaluation = {}
    }

    let evaluation = alleleassesment.evaluation
    for (let key of ['prediction', 'classification', 'external', 'frequency', 'reference']) {
        if (!(key in evaluation)) {
            evaluation[key] = {
                comment: ''
            }
        }
    }

    if (!('acmg' in evaluation)) {
        evaluation.acmg = {}
    }
    if (!('included' in evaluation.acmg)) {
        evaluation.acmg.included = []
    }
    if (!('suggested' in evaluation.acmg)) {
        evaluation.acmg.suggested = []
    }

    //
    // Migrations
    //

    // Move and rename alleleState.autoReuseAlleleAssessmentCheckedId
    if ('autoReuseAlleleAssessmentCheckedId' in alleleState) {
        alleleState.alleleassessment.reuseCheckedId = alleleState.autoReuseAlleleAssessmentCheckedId
        delete alleleState.autoReuseAlleleAssessmentCheckedId
    }

    // Move and rename alleleState.alleleAssessmentCopiedFromId
    if ('alleleAssessmentCopiedFromId' in alleleState) {
        alleleState.alleleassessment.copiedFromId = alleleState.alleleAssessmentCopiedFromId
        delete alleleState.alleleAssessmentCopiedFromId
    }

    // Move and rename alleleState.alleleReportCopiedFromId
    if ('alleleReportCopiedFromId' in alleleState) {
        alleleState.allelereport.copiedFromId = alleleState.alleleReportCopiedFromId
        delete alleleState.alleleReportCopiedFromId
    }
}

export function checkAlleleStateModel(alleleState) {
    // We need to check every key for itself, as we can have older, partial models as input
    if (!('alleleassessment' in alleleState)) {
        alleleState.alleleassessment = {}
    }

    if (!('referenceassessments' in alleleState)) {
        alleleState.referenceassessments = []
    }

    if (!('allelereport' in alleleState)) {
        alleleState.allelereport = {
            evaluation: {
                comment: ''
            }
        }
    }

    if (!('report' in alleleState)) {
        alleleState.report = {
            included: false
        }
    }

    if (!('verification' in alleleState)) {
        alleleState.verification = null
    }

    checkAlleleAssessmentModel(alleleState)
}

/**
 * Helper class for working with alleleState objects
 * (alleleState objects are part of the interpretation's state,
 * describing the state for one allele).
 */

export function setupAlleleState(allele, alleleState) {
    // If not existing, return the object from the state, or create empty one

    checkAlleleStateModel(alleleState)
    if (allele.allele_assessment) {
        alleleState.presented_alleleassessment_id = allele.allele_assessment.id
    }

    if (allele.allele_report) {
        alleleState.presented_allelereport_id = allele.allele_report.id
    }

    copyAlleleAssessmentToState(allele, alleleState)
    // The copied alleleassessment can have an older model that is lacking fields.
    // We need to check the model and add any missing fields to make it up to date.
    checkAlleleAssessmentModel(alleleState)

    copyAlleleReportToState(allele, alleleState)
}

/**
 * Copies any existing allele's alleleassessment into the alleleState.
 * To be used when the user want's to edit the existing assessment.
 * @param {Object} allele   Allele to copy alleleassessment from.
 * @param {Object} alleleState   Allele state to modify
 * @param {Boolean} forceCopy Copy into alleleState regardless
 */
export function copyAlleleAssessmentToState(allele, alleleState, forceCopy = false) {
    // Check if remote alleleassessment is newer, if so copy it in again.
    if (
        allele.allele_assessment &&
        (forceCopy ||
            (!alleleState.alleleassessment.copiedFromId ||
                allele.allele_assessment.id > alleleState.alleleassessment.copiedFromId))
    ) {
        alleleState.alleleassessment.evaluation = deepCopy(allele.allele_assessment.evaluation)
        alleleState.alleleassessment.attachment_ids = deepCopy(
            allele.allele_assessment.attachment_ids
        )
        alleleState.alleleassessment.classification = allele.allele_assessment.classification
        alleleState.alleleassessment.copiedFromId = allele.allele_assessment.id
    }
}

/**
 * Copies any existing allele's report into the alleleState.
 * To be used when the user want's to edit the existing report.
 * @param {Object} allele   Allele to copy report from.
 * @param {Object} alleleState   Allele state to modify
 * @param {Boolean} forceCopy Copy into alleleState regardless
 */
export function copyAlleleReportToState(allele, alleleState, forceCopy = false) {
    // Check if date of remote allelereport is newer, if so copy it in again.
    if (
        allele.allele_report &&
        (forceCopy ||
            (!alleleState.allelereport.copiedFromId ||
                allele.allele_report.id > alleleState.allelereport.copiedFromId))
    ) {
        alleleState.allelereport.evaluation = deepCopy(allele.allele_report.evaluation)
        alleleState.allelereport.copiedFromId = allele.allele_report.id
    }
}
