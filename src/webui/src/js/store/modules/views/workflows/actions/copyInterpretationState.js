import { deepCopy } from '../../../../../util'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'

export default function copyInterpretationState({ state, resolve }) {
    const selectedInterpretation = resolve.value(getSelectedInterpretation)
    state.set('views.workflows.interpretation.state', deepCopy(selectedInterpretation.state))
    state.set(
        'views.workflows.interpretation.userState',
        deepCopy(selectedInterpretation.user_state)
    )
    let isOngoing = Boolean(selectedInterpretation.status === 'Ongoing')
    state.set('views.workflows.interpretation.isOngoing', isOngoing)
}
