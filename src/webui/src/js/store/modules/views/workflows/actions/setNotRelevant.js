export default function setNotRelevant({ props, state }) {
    const { alleleId, notRelevant } = props
    state.set(
        `views.workflows.interpretation.state.allele.${alleleId}.analysis.notrelevant`,
        notRelevant
    )
}
