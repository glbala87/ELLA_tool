import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

function defaultInterpretationState() {
    return {
        status: 'Not started',
        state: {},
        user_state: {}
    }
}

export default Compute(
    state`views.workflows.data.interpretations`,
    state`views.workflows.interpretation.selectedId`,
    (interpretations, selectedInterpretationId) => {
        if (selectedInterpretationId == null) {
            return null
        }
        let interpretation = null
        if (selectedInterpretationId === 'current') {
            if (interpretations.length === 0) {
                return defaultInterpretationState()
            } else {
                let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
                interpretation = doneInterpretations[doneInterpretations.length - 1]
            }
        } else {
            interpretation = interpretations.filter((i) => i.id === selectedInterpretationId)[0]
        }

        return interpretation
    }
)
