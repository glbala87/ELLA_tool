import { deepCopy } from '../../../../../util'

export default function selectDefaultInterpretation({ state }) {
    let interpretations = state.get('views.workflows.data.interpretations')
    let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
    let lastInterpretation = interpretations[interpretations.length - 1]

    // If an interpretation is Ongoing, we assign it directly
    let isOngoing = Boolean(lastInterpretation && lastInterpretation.status === 'Ongoing')
    let selectedId
    if (lastInterpretation && lastInterpretation.status === 'Ongoing') {
        isOngoing = true
        selectedId = lastInterpretation.id
    } else if (doneInterpretations.length) {
        // Otherwise, make a copy of the last historical one to act as "current" entry in the dropdown.
        // This lets the user see the latest data in the UI
        selectedId = 'current'
    } else if (lastInterpretation) {
        selectedId = lastInterpretation.id
    } else {
        // If we have no history, set interpretation.selected to empty representation
        // only used for the view to have a model so it doesn't crash.
        // It will never be stored in backend. This should only happen when type: allele and
        // there is not existing interpretation in the backend
        if (state.get('views.workflows.type') === 'analysis') {
            throw Error(
                "No interpretations loaded when type == analysis. This shouldn't be possible."
            )
        }

        if (!state.get('views.workflows.allele')) {
            throw Error('Missing allele in state data when type == allele')
        }
        selectedId = 'current'
    }
    state.set('views.workflows.interpretation.isOngoing', isOngoing)
    state.set('views.workflows.interpretation.selectedId', selectedId)
}
