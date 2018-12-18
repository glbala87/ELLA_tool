export default function saveOverviewState({ state, storage }) {
    const overviewState = state.get('views.overview.state')
    storage.set('overviewState', overviewState)
}
