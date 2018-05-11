import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingReferenceAssessments({ state, resolve }) {
    const alleles = state.get('views.workflows.data.alleles')

    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleState = resolve.value(getAlleleState(alleleId))

        // Don't keep any user content when alleleassessment is reused
        if (alleleState.alleleassessment.reuse) {
            state.set(
                `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments`,
                []
            )
        }

        // (Re)populate
        if ('reference_assessments' in allele) {
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
                    // If it does exist, check whether allele's existing is newer and we should reuse it
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
