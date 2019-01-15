import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getSelectedInterpretation from './getSelectedInterpretation'

export default Compute(
    state`views.workflows.interpretation.isOngoing`,
    state`views.workflows.interpretation.selectedId`,
    state`app.user`,
    (ongoing, selectedId, user, get) => {
        if (selectedId == null) {
            return true
        }
        const interpretation = get(getSelectedInterpretation)
        return !ongoing || (interpretation && interpretation.user.id !== user.id)
    }
)
