import deepCopy from '../../../../../../util'
import getReferenceAssessment from '../computed/getReferenceAssessment'
import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingReferenceAssessments({ state, resolve, props }) {
    const alleles = state.get('views.workflows.data.alleles')
    const references = state.get('views.workflows.data.references')
    const config = state.get('app.config')

    for (let [alleleId, allele] of Object.entries(alleles)) {
        if ('reference_assessments' in allele) {
            const alleleState = resolve.value(getAlleleState(alleleId))
            for (let referenceAssessment of allele.reference_assessments) {
                // Check whether it exists in state already
                const raIdx = alleleState.referenceassessments.findIndex((ra) => {
                    return (
                        ra.reference_id === referenceAssessment.reference_id &&
                        ra.allele_id === referenceAssessment.allele_id
                    )
                })

                const reusedReferenceAssessment = {
                    id: referenceAssessment.id,
                    reference_id: referenceAssessment.reference_id,
                    allele_id: referenceAssessment.allele_id,
                    reuseCheckedId: referenceAssessment.id,
                    reuse: true
                }

                if (raIdx < 0) {
                    // Doesn't exist already -> add and set to reuse
                    state.push(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments`,
                        reusedReferenceAssessment
                    )
                } else {
                    // If if does exist, check whether allele's existing is newer and we should reuse it
                    const existing = state.get(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}`
                    )
                    if (
                        !('reuseCheckedId' in existing) ||
                        existing.reuseCheckedId < referenceAssessment.id
                    ) {
                        state.set(
                            `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}`,
                            reusedReferenceAssessment
                        )
                    }
                }
            }
        }
    }
}
