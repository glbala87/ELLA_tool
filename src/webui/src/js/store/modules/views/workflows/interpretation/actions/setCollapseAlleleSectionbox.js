export default function setCollapseAlleleSectionbox({ state, props }) {
    const { collapsed, section, alleleId } = props
    state.set(
        `views.workflows.interpretation.selected.user_state.allele.${alleleId}.sections.${section}.collapsed`,
        collapsed
    )
}
