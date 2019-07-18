import thenBy from 'thenby'
import { deepCopy } from '../../../../../../../util'

const FIELDS = ['classification', 'frequency', 'external', 'prediction', 'reference']

export default function getClassificationDetails({ http, path, state }) {
    const viewMode = state.get('views.workflows.modals.alleleAssessmentHistory.selectedViewMode')
    const alleleAssessments = state.get(
        'views.workflows.modals.alleleAssessmentHistory.data.alleleAssessments'
    )
    const alleleAssessment = state.get(
        'views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment'
    )

    const details = {}

    for (const f of FIELDS) {
        details[f] = ''
    }

    if (!alleleAssessment) {
        return path.success({ result: details })
    }

    if (viewMode === 'diff') {
        // Package together all comments we need to diff into an array
        // so we can diff everything on one request
        const payload = []
        const alleleAssessmentIdx = alleleAssessments.findIndex(
            (aa) => aa.id === alleleAssessment.id
        )
        if (alleleAssessmentIdx + 1 >= alleleAssessments.length) {
            return path.error()
        }
        const previousAlleleAssessment = alleleAssessments[alleleAssessmentIdx + 1]

        for (const f of FIELDS) {
            payload.push({
                old: previousAlleleAssessment.evaluation[f].comment,
                new: alleleAssessment.evaluation[f].comment
            })
        }

        // Append ACMG comments diff at the end.
        // We need to keep a list of ACMG code UUIDs that we diffed
        // in order to map the diff result back to each code
        const currentAcmg = alleleAssessment.evaluation.acmg.included
        const prevAcmg = previousAlleleAssessment.evaluation.acmg.included

        const toDiffAcmgUuids = []
        for (const code of currentAcmg) {
            const prev = prevAcmg.find((c) => c.code === code.code && c.uuid === code.uuid)
            if (prev) {
                toDiffAcmgUuids.push(code.uuid)
                payload.push({
                    old: prev.comment,
                    new: code.comment
                })
            }
        }

        console.warn('ACMG DIFF IS NOT IMPLEMENTED YET!!!')

        return http
            .post(`reports/diff/`, payload)
            .then((response) => {
                let fIdx = 0
                for (const f of FIELDS) {
                    details[f] = response.result[fIdx].result
                    fIdx += 1
                }

                // Add ACMG codes where code is the same between old and new,
                // with their diffed comment
                details.acmg = []
                for (const diffAcmgUuid of toDiffAcmgUuids) {
                    const acmgCode = deepCopy(currentAcmg.find((c) => c.uuid === diffAcmgUuid))
                    acmgCode.comment = response.result[fIdx].result
                    details.acmg.push(acmgCode)
                    fIdx += 1
                }

                // Add added codes
                details.addedAcmg = []
                for (const code of currentAcmg) {
                    if (!prevAcmg.find((c) => c.uuid === code.uuid && c.code === code.code)) {
                        details.addedAcmg.push(code)
                    }
                }

                // Add removed codes
                details.removedAcmg = []
                for (const code of prevAcmg) {
                    if (!currentAcmg.find((c) => c.uuid === code.uuid && c.code === code.code)) {
                        details.removedAcmg.push(code)
                    }
                }

                return path.success({ result: details })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    } else {
        for (const f of FIELDS) {
            details[f] = alleleAssessment.evaluation[f].comment
        }

        details['acmg'] = alleleAssessment.evaluation.acmg.included
        return path.success({ result: details })
    }
}
