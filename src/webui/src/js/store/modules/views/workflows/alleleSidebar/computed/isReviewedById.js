import { Compute } from 'cerebral'
import getAlleleReviewedStatus from '../../interpretation/computed/getAlleleReviewedStatus'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (const [alleleId, allele] of Object.entries(alleles)) {
            result[alleleId] = get(getAlleleReviewedStatus(allele))
        }
        return result
    })
}
