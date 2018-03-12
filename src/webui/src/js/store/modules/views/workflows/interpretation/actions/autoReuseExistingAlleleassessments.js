import getClassification from '../computed/getClassification'
import getAlleleState from '../computed/getAlleleState'
import isAlleleAssessmentOutdated from '../../../../../common/computes/isAlleleAssessmentOutdated'

export default function autoReuseExistingAlleleassessments({ state, resolve }) {
    const alleles = state.get('views.workflows.data.alleles')
    const config = state.get('app.config')
    const changedAlleleIds = []

    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        if (allele.allele_assessment) {
            // Check whether it's outdated, if so force disabling reuse.
            const isOutdated = resolve.value(isAlleleAssessmentOutdated(allele))
            if (isOutdated) {
                state.set(
                    `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.reuse`,
                    false
                )
            } else if (
                !('reuseCheckedId' in alleleState.alleleassessment) ||
                alleleState.alleleassessment.reuseCheckedId < allele.allele_assessment.id
            ) {
                if (!isOutdated) {
                    state.set(
                        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.reuse`,
                        true
                    )
                    changedAlleleIds.push(alleleId)
                }
                state.set(
                    `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.reuseCheckedId`,
                    allele.allele_assessment.id
                )
            }
            // Copying in the existing alleleassessment into alleleState is handled elsewhere
        }
    }
    return { changedAlleleIds }
}
