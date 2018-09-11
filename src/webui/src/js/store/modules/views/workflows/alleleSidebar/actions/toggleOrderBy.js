export default function toggleOrderBy({ state, props }) {
    const orderBy = state.get(props.orderByPath)
    const { orderByPath, key } = props

    // Acts as a three-state toggle:
    // - First time user clicks on key, sort by key
    // - Second time, reverse order
    // - Third time, reset to default sort
    if (orderBy.key === key) {
        if (!orderBy.reverse) {
            state.set(`${orderByPath}.reverse`, true)
        } else {
            // Reset to default sort
            state.set(`${orderByPath}.key`, null)
            state.set(`${orderByPath}.reverse`, false)
        }
    } else {
        state.set(`${orderByPath}.key`, key)
    }
}
