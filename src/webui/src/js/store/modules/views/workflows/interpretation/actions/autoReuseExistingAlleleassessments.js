import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingAlleleassessments({ state, resolve }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const checkReportAlleleIds = []
    const newAlleleAssessmentAlleleIds = []

    for (let [alleleId, allele] of Object.entries(alleles)) {
        if (!allele.allele_assessment) {
            continue
        }
        const alleleState = resolve.value(getAlleleState(alleleId))

        const hasNewAlleleAssessment =
            !('reuseCheckedId' in alleleState.alleleassessment) ||
            alleleState.alleleassessment.reuseCheckedId < allele.allele_assessment.id
        const isReused = alleleState.alleleassessment.reuse

        if (hasNewAlleleAssessment || isReused) {
            const reusedAlleleAssessment = {
                allele_id: allele.id,
                reuse: true,
                reuseCheckedId: allele.allele_assessment.id
            }

            state.set(
                `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment`,
                reusedAlleleAssessment
            )
        }

        if (hasNewAlleleAssessment) {
            checkReportAlleleIds.push(allele.id)
            newAlleleAssessmentAlleleIds.push(allele.id)
        }
    }
    return { checkReportAlleleIds, newAlleleAssessmentAlleleIds }
}
