import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default alleleId => {
    return Compute(
        alleleId,
        state`views.workflows.interpretation.selected`,
        (alleleId, interpretation, get) => {
            if (!interpretation) {
                return
            }
            return interpretation.state.allele[alleleId]
        }
    )
}
