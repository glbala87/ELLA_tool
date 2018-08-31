import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.analysis`, (analysis) => {
    if (!analysis) {
        return false
    }
    return Boolean(analysis.warnings)
})
