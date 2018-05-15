import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default (alleleId) => {
    return Compute(
        alleleId,
        state`views.workflows.interpretation.selected`,
        (alleleId, interpretation, get) => {
            return interpretation.user_state.allele[alleleId]
        }
    )
}
