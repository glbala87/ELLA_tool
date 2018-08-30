import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretationlogs`, (logs) => {
    if (!logs) {
        return null
    }
    const sortedPriorities = Object.values(logs)
        .sort(thenBy('date_created', -1))
        .filter((l) => l.priority !== null)
        .map((l) => l.priority)
    console.log(sortedPriorities)
    if (sortedPriorities.length) {
        return sortedPriorities[0]
    }
    return null
})
