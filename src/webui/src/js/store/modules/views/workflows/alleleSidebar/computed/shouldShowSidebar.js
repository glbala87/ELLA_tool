import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default Compute(
    state`views.workflows.type`,
    state`views.workflows.selectedComponent`,
    state`views.workflows.data.alleles`,
    (workflowType, selectedComponent, alleles) => {
        if (workflowType === 'allele') {
            return false
        } else {
            if (!alleles) {
                return
            }
            return selectedComponent !== 'Info'
        }
    }
)
