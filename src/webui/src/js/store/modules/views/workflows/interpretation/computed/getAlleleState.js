import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (alleleId) => {
    return Compute(
        alleleId,
        state`views.workflows.interpretation.state.allele`,
        (alleleId, interpretationStateAllele) => {
            if (!interpretationStateAllele) {
                return
            }
            return interpretationStateAllele[alleleId]
        }
    )
}
