import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        result[alleleId] = allele.tags.includes('has_references')
    }
    return result
})
