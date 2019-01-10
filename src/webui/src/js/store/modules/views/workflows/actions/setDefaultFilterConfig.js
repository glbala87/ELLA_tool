export default function({ state }) {
    let stateFilterConfigId = state.get(
        'views.workflows.interpretation.selected.state.filterconfigId'
    )
    let availableFilterConfigIds = state
        .get('views.workflows.data.filterconfigs')
        .map((fc) => fc.id)
    if (!availableFilterConfigIds.includes(stateFilterConfigId)) {
        let defaultFilterConfigId = state.get('views.workflows.data.filterconfigs')[0].id
        state.set(
            'views.workflows.interpretation.selected.state.filterconfigId',
            defaultFilterConfigId
        )
    }
}
