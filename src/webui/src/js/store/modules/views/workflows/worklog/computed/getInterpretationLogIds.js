import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretationlogs`, (logs) => {
    if (!logs) {
        return []
    }
    return Object.values(logs)
        .sort(thenBy('date_created'))
        .map((l) => l.id)
})
