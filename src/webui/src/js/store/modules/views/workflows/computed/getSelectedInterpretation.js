import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import { deepCopy } from '../../../../../util'

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
        let interpretation
        if (selectedInterpretationId === 'current') {
            if (interpretations.length === 0) {
                return defaultInterpretationState()
            } else {
                interpretation = interpretations[interpretations.length - 1]
            }
        } else {
            interpretation = interpretations.filter((i) => i.id === selectedInterpretationId)[0]
        }

        return interpretation

        interpretation = deepCopy(interpretation)
        delete interpretation.state
        delete interpretation.user_state
        delete interpretation.excluded_allele_ids
        delete interpretation.allele_ids

        return interpretation
    }
)
