import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default function setDefaultFilterConfig({ state, resolve }) {
    const stateFilterConfigId = state.get('views.workflows.interpretation.state.filterconfigId')
    const availableFilterConfigIds = state
        .get('views.workflows.data.filterconfigs')
        .map((fc) => fc.id)

    const selectedInterpretation = resolve.value(getSelectedInterpretation)
    const current = state.get('views.workflows.interpretation.selectedId') === 'current'
    const isDone = selectedInterpretation.status === 'Done'

    // Set default filter config when showing current data or in an ongoing interpretation,
    // and the selected filter config is not available for filtering
    // OR interpretation is done, but filterconfigId is not set in state (historical data only)
    if (
        ((current || !isDone) && !availableFilterConfigIds.includes(stateFilterConfigId)) ||
        (isDone && !stateFilterConfigId)
    ) {
        let defaultFilterConfigId = state.get('views.workflows.data.filterconfigs')[0].id
        state.set('views.workflows.interpretation.state.filterconfigId', defaultFilterConfigId)
    }

    if (!state.get('views.workflows.interpretation.state.filterconfigId')) {
        throw Error('Filter config ID not set in state. This should not be possible')
    }
}
