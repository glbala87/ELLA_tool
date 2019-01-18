import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.interpretation.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        if ('samples' in allele) {
            result[alleleId] = allele.tags.includes('homozygous')
        } else {
            result[alleleId] = false
        }
    }
    return result
})
