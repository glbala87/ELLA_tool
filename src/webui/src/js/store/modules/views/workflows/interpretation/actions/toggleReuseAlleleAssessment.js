export default function toggleReuseAlleleAssessment({ state, resolve, props }) {
    const { alleleId } = props
    const copyExistingAlleleAssessmentAlleleIds = []
    const allele = state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
    if (!allele.allele_assessment) {
        throw Error(`Cannot toggle non-existing alleleassessment for allele id ${alleleId}`)
    }
    const alleleAssessment = state.get(
        `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment`
    )
    if (alleleAssessment.reuse) {
        state.set(
            `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment.reuse`,
            false
        )
        copyExistingAlleleAssessmentAlleleIds.push(alleleId)
    } else {
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
    return { copyExistingAlleleAssessmentAlleleIds }
}
