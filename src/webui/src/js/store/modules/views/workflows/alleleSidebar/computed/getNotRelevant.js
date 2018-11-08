import { Compute } from 'cerebral'
import getNotRelevant from '../../interpretation/computed/getNotRelevant'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (const alleleId of Object.keys(alleles)) {
            result[alleleId] = get(getNotRelevant(alleleId))
        }
        return result
    })
}
