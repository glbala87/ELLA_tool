export default function saveOverviewState({ props, state, storage }) {
    const overviewState = state.get('views.overview.state')
    storage.set('overviewState', overviewState)
}
