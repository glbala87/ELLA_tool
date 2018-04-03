import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default Compute(state`views.workflows.data.alleles`, (alleles) => {
    const result = {}
    if (!alleles) {
        return
    }
    for (let [alleleId, allele] of Object.entries(alleles)) {
        result[alleleId] =
            'HGMD' in allele.annotation.external && allele.annotation.external.HGMD.tag
    }
    return result
})
