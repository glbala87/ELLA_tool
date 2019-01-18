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
        if (selectedInterpretationId === null || selectedInterpretationId === undefined) {
            return null
        }
        let interpretation = null
        if (selectedInterpretationId === 'current') {
            if (interpretations.length === 0) {
                // In allele workflow, this can happen. Analysis should create interpretation objects upon import
                return defaultInterpretationState()
            } else {
                // The state of the last done entry will be copied over to `views.workflows.interpretation`.
                // The latest annotation is fetched from backend when selectedId === 'current'
                let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
                interpretation = doneInterpretations[doneInterpretations.length - 1]
            }
        } else {
            interpretation = interpretations.find((i) => i.id === selectedInterpretationId)
        }

        return interpretation
    }
)
