import { Compute } from 'cerebral'
import getWarnings from '../../interpretation/computed/getWarnings'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (const [alleleId, allele] of Object.entries(alleles)) {
            result[alleleId] = get(getWarnings(allele))
        }
        return result
    })
}
