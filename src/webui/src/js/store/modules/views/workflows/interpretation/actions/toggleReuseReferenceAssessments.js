import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingReferenceAssessments({ state, resolve, props }) {
    const { alleleId } = props
    const allele = state.get(`views.workflows.data.alleles.${alleleId}`)

    if ('reference_assessments' in allele) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        for (let referenceAssessment of allele.reference_assessments) {
            // Find referenceassessment in state
            const raIdx = alleleState.referenceassessments.findIndex((ra) => {
                return (
                    ra.reference_id === referenceAssessment.reference_id &&
                    ra.allele_id === referenceAssessment.allele_id
                )
            })

            if (raIdx < 0) {
                throw Error(
                    "Existing referenceassessment status is not found in state, this shouldn't be possible."
                )
            } else {
                state.toggle(
                    `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}.reuse`
                )
                // For now, 'id' and reuse goes hand in hand
                if (
                    state.get(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}.reuse`
                    )
                ) {
                    state.set(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}.id`,
                        referenceAssessment.id
                    )
                } else {
                    state.unset(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}.id`
                    )
                }
            }
        }
    }
}
