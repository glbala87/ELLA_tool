import { deepCopy } from '../../../../../util'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default function prepareSelectedInterpretation({ state, resolve }) {
    const selectedInterpretation = resolve.value(getSelectedInterpretation)
    state.set('views.workflows.interpretation.state', deepCopy(selectedInterpretation.state))
    state.set(
        'views.workflows.interpretation.userState',
        deepCopy(selectedInterpretation.user_state)
    )

    // TODO: Should be moved to loadInterpretationData when endpoint is available
    if (selectedInterpretation.allele_ids == null) {
        if (state.get('views.workflows.type') === 'analysis') {
            throw Error(
                "No allele ids on interpretation object when type == analysis. This shouldn't be possible."
            )
        }

        if (!state.get('views.workflows.allele')) {
            throw Error('Missing allele in state data when type == allele')
        }

        state.set('views.workflows.interpretation.data.filteredAlleleIds.allele_ids', [
            state.get(`views.workflows.id`)
        ])
        state.set('views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids', {})
    } else {
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.allele_ids',
            selectedInterpretation.allele_ids
        )
        state.set(
            'views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids',
            selectedInterpretation.excluded_allele_ids
        )
    }
}
