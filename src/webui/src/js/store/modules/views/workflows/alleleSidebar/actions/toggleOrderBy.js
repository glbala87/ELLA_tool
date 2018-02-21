export default function toggleOrderBy({ state, props }) {
    const orderBy = state.get('views.workflows.alleleSidebar.orderBy')
    const { section, key } = props

    // Acts as a three-state toggle:
    // - First time user clicks on key, sort by key
    // - Second time, reverse order
    // - Third time, reset to default sort
    if (orderBy[section].key === key) {
        if (!orderBy[section].reverse) {
            state.set(`views.workflows.alleleSidebar.orderBy.${section}.reverse`, true)
        } else {
            // Reset to default sort
            state.set(`views.workflows.alleleSidebar.orderBy.${section}.key`, null)
            state.set(`views.workflows.alleleSidebar.orderBy.${section}.reverse`, false)
        }
    } else {
        state.set(`views.workflows.alleleSidebar.orderBy.${section}.key`, key)
    }
}
