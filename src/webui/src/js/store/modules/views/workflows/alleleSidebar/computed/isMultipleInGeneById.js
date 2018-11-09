import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default (alleles) => {
    return Compute(alleles, (alleles) => {
        if (!alleles) {
            return {}
        }
        const result = {}
        for (let [alleleId, allele] of Object.entries(alleles)) {
            let otherAlleles = Object.values(alleles).filter((a) => a !== allele)

            let otherAlleleGenes = []
            for (let otherAllele of otherAlleles) {
                otherAlleleGenes.push(...otherAllele.annotation.filtered.map((f) => f.symbol))
            }
            let ourGenes = allele.annotation.filtered.map((f) => f.symbol)
            result[alleleId] = ourGenes.some((s) => otherAlleleGenes.includes(s))
        }
        return result
    })
}
