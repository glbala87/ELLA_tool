import getClassification from '../computed/getClassification'
import getAlleleState from '../computed/getAlleleState'
import isAlleleAssessmentOutdated from '../../../../../common/computes/isAlleleAssessmentOutdated'

export default function autoReuseExistingAlleleassessments({ state, resolve }) {
    const alleles = state.get('views.workflows.data.alleles')
    const config = state.get('app.config')
    const checkReportAlleleIds = []
    const copyExistingAlleleAssessmentAlleleIds = []

    for (let [alleleId, allele] of Object.entries(alleles)) {
        if (!allele.allele_assessment) {
            continue
        }
        const alleleState = resolve.value(getAlleleState(alleleId))
        const isOutdated = resolve.value(isAlleleAssessmentOutdated(allele))
        if (
            !('reuseCheckedId' in alleleState.alleleassessment) ||
            alleleState.alleleassessment.reuseCheckedId < allele.allele_assessment.id
        ) {
            const reusedAlleleAssessment = {
                allele_id: allele.id,
                reuse: !isOutdated,
                reuseCheckedId: allele.allele_assessment.id
            }
            checkReportAlleleIds.push(allele.id)
            if (isOutdated) {
                copyExistingAlleleAssessmentAlleleIds.push(allele.id)
            }
            state.set(
                `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment`,
                reusedAlleleAssessment
            )
        } else if (isOutdated) {
            state.set(
                `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.reuse`,
                false
            )
        }
    }
    return { checkReportAlleleIds, copyExistingAlleleAssessmentAlleleIds }
}
