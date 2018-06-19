import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (alleleId) => {
    return Compute(
        alleleId,
        state`views.workflows.interpretation.selected`,
        (alleleId, interpretation) => {
            if (!interpretation || !interpretation.state || !interpretation.state.allele) {
                return
            }
            return interpretation.state.allele[alleleId]
        }
    )
}
