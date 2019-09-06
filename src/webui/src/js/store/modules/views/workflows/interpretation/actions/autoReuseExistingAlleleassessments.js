import getAlleleState from '../computed/getAlleleState'

export default function autoReuseExistingAlleleassessments({ state, resolve }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const checkReportAlleleIds = []

    for (let [alleleId, allele] of Object.entries(alleles)) {
        if (!allele.allele_assessment) {
            continue
        }
        const alleleState = resolve.value(getAlleleState(alleleId))

        const isReusedNotCheckedOrOld =
            !('reuseCheckedId' in alleleState.alleleassessment) ||
            alleleState.alleleassessment.reuseCheckedId < allele.allele_assessment.id
        const isReused = alleleState.alleleassessment.reuse

        if (isReusedNotCheckedOrOld || isReused) {
            const reusedAlleleAssessment = {
                allele_id: allele.id,
                reuse: true,
                reuseCheckedId: allele.allele_assessment.id
            }
            checkReportAlleleIds.push(allele.id)

            state.set(
                `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment`,
                reusedAlleleAssessment
            )
        }
    }
    return { checkReportAlleleIds }
}
