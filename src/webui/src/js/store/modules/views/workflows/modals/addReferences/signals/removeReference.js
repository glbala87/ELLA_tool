export default [
    ({ state, props }) => {
        const { refId } = props
        var userReferenceIds = state.get(`views.workflows.modals.addReferences.userReferenceIds`)
        userReferenceIds = userReferenceIds.filter((x) => x !== refId)
        state.set(`views.workflows.modals.addReferences.userReferenceIds`, userReferenceIds)
    }
]
