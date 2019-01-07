import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        if ('samples' in allele) {
            result[alleleId] = allele.samples.some((s) => s.genotype.needs_verification)
        } else {
            result[alleleId] = false
        }
    }
    return result
})
