export default function loadOverviewState({ props, state, storage }) {
    state.set('views.overview.state', storage.get('overviewState', {}))
}
