import { deepCopy } from '../../../../../util'

export default function prepareSelectedInterpretation({ state }) {
    let interpretations = state.get('views.workflows.data.interpretations')
    let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
    let lastInterpretation = interpretations[interpretations.length - 1]

    // If an interpretation is Ongoing, we assign it directly
    let isOngoing = Boolean(lastInterpretation && lastInterpretation.status === 'Ongoing')
    if (lastInterpretation && lastInterpretation.status === 'Ongoing') {
        isOngoing = true
        state.set('views.workflows.interpretation.selectedId', lastInterpretation.id)
        state.set('views.workflows.interpretation.state', deepCopy(lastInterpretation.state))
        state.set(
            'views.workflows.interpretation.userState',
            deepCopy(lastInterpretation.user_state)
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.allele_ids',
            lastInterpretation.allele_ids
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
            lastInterpretation.excluded_allele_ids
        )
    } else if (doneInterpretations.length) {
        // Otherwise, make a copy of the last historical one to act as "current" entry in the dropdown.
        // This lets the user see the latest data in the UI
        let currentInterpretation = deepCopy(doneInterpretations[doneInterpretations.length - 1])
        state.set('views.workflows.interpretation.selectedId', 'current')
        state.set('views.workflows.interpretation.state', deepCopy(currentInterpretation.state))
        state.set(
            'views.workflows.interpretation.userState',
            deepCopy(currentInterpretation.user_state)
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.allele_ids',
            currentInterpretation.allele_ids
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
            currentInterpretation.excluded_allele_ids
        )
    } else if (lastInterpretation) {
        state.set('views.workflows.interpretation.selectedId', lastInterpretation.id)
        state.set('views.workflows.interpretation.state', deepCopy(lastInterpretation.state))
        state.set(
            'views.workflows.interpretation.userState',
            deepCopy(lastInterpretation.user_state)
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.allele_ids',
            lastInterpretation.allele_ids
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
            lastInterpretation.excluded_allele_ids
        )
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

        state.set('views.workflows.interpretation', {
            // genepanel_name: state.get('views.workflows.data.genepanel.name'),
            // genepanel_version: state.get('views.workflows.data.genepanel.version'),
            state: {},
            userState: {},
            // status: 'Not started',
            // allele_ids: [state.get('views.workflows.allele.id')]

            selectedId: 'current'
        })
        state.set('views.workflows.interpretation.data.filteredAlleleIds', {
            allele_ids: [state.get('views.workflows.id')]
        })
    }
    state.set('views.workflows.interpretation.isOngoing', isOngoing)
}
