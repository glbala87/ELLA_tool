import { deepCopy } from '../../../util'

export function prepareAlleleAssessmentModel(alleleAssessment) {
    if (!('attachment_ids' in alleleAssessment)) {
        alleleAssessment.attachment_ids = []
    }

    if (!('reuse' in alleleAssessment)) {
        alleleAssessment.reuse = false
    }

    if (!('classification' in alleleAssessment)) {
        alleleAssessment.classification = null
    }

    if (!('evaluation' in alleleAssessment)) {
        alleleAssessment.evaluation = {}
    }

    let evaluation = alleleAssessment.evaluation
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
}

export function prepareAlleleStateModel(alleleState) {
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
