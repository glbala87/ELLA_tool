import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretations`, (interpretations) => {
    return interpretations && interpretations.length
})
