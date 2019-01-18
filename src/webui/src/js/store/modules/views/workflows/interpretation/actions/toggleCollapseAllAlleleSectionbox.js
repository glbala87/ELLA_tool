export default function toggleCollapseAllAlleleSectionbox({ state }) {
    const alleleId = state.get('views.workflows.selectedAllele')

    // If all are collapsed -> uncollapse, otherwise collapse all
    const sections = state.get(
        `views.workflows.interpretation.userState.allele.${alleleId}.sections`
    )
    const sectionKeys = state.get(`views.workflows.components.Classification.sectionKeys`)
    const allCollapsed = sectionKeys.every((k) => (k in sections ? sections[k].collapsed : false))
    for (let key of sectionKeys) {
        state.set(
            `views.workflows.interpretation.userState.allele.${alleleId}.sections.${key}.collapsed`,
            !allCollapsed
        )
    }
}
