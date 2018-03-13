import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, alleles => {
    return Object.keys(alleles).length > 0
})
