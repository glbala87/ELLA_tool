import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretationlogs`, (logData) => {
    if (!logData) {
        return null
    }
    const sortedWarningCleared = logData.logs
        .sort(thenBy('date_created', -1))
        .filter((l) => l.warning_cleared !== null)
        .map((l) => l.warning_cleared)

    if (sortedWarningCleared.length) {
        return sortedWarningCleared[0]
    }
    return null
})
