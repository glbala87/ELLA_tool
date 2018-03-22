import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

export default Compute(state`views.workflows.data.alleles`, (alleles, get) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleState = get(getAlleleState(alleleId))
        result[alleleId] = alleleState.verification || null
    }
    return result
})
