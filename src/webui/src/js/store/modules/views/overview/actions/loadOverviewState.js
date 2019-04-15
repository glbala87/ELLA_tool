export default function loadOverviewState({ state, storage }) {
    state.set('views.overview.state', storage.get('overviewState', {}))
}
