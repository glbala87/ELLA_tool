import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getManuallyAddedAlleleIds from '../../interpretation/computed/getManuallyAddedAlleleIds'

export default (alleles) => {
    return Compute(alleles, getManuallyAddedAlleleIds, (alleles, manuallyAddedAlleleIds) => {
        if (!alleles) {
            return {}
        }
        const result = {}
        for (let [alleleId, allele] of Object.entries(alleles)) {
            result[alleleId] = manuallyAddedAlleleIds.includes(allele.id)
        }
        return result
    })
}
