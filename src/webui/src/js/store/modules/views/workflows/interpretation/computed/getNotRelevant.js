import { Compute } from 'cerebral'
import getAlleleState from './getAlleleState'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (let [alleleId, allele] of Object.entries(alleles)) {
            const alleleState = get(getAlleleState(alleleId))

            result[alleleId] = alleleState ? alleleState.analysis.notrelevant : null
        }
        return result
    })
}
