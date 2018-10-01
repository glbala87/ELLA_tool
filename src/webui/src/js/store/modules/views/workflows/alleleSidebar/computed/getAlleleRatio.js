import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return result
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        result[alleleId] = allele.samples
            .map((s) => (s.genotype.allele_ratio ? s.genotype.allele_ratio.toFixed(2) : '-'))
            .join(', ')
    }
    return result
})
