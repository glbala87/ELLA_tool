import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default function setDefaultFilterConfig({ state, resolve }) {
    const stateFilterConfigId = state.get('views.workflows.interpretation.state.filterconfigId')
    const availableFilterConfigIds = state
        .get('views.workflows.data.filterconfigs')
        .map((fc) => fc.id)

    const selectedInterpretation = resolve.value(getSelectedInterpretation)
    const current = state.get('views.workflows.interpretation.selectedId') === 'current'
    const isDone = selectedInterpretation.status === 'Done'

    // Only set default filter config when showing current data or in an ongoing interpretation,
    // and the selected filter config is not available for filtering
    if ((current || !isDone) && !availableFilterConfigIds.includes(stateFilterConfigId)) {
        let defaultFilterConfigId = state.get('views.workflows.data.filterconfigs')[0].id
        state.set('views.workflows.interpretation.state.filterconfigId', defaultFilterConfigId)
    }
}
