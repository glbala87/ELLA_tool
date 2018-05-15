import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        if ('samples' in allele) {
            result[alleleId] = allele.samples[0].genotype.homozygous // TODO: Make sure multiple samples pick correct sample
        } else {
            result[alleleId] = false
        }
    }
    return result
})
