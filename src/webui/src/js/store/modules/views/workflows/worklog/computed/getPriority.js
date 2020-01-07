import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretationlogs`, (logData) => {
    if (!logData) {
        return null
    }
    const sortedPriorities = logData.logs
        .sort(thenBy('date_created', -1))
        .filter((l) => l.priority !== null)
        .map((l) => l.priority)
    if (sortedPriorities.length) {
        return sortedPriorities[0]
    }
    return null
})
