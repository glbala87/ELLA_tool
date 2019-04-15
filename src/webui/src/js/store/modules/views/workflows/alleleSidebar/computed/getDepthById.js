import { Compute } from 'cerebral'

export default (alleles) => {
    return Compute(alleles, (alleles) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (let [alleleId, allele] of Object.entries(alleles)) {
            if (allele.samples) {
                result[alleleId] = allele.samples
                    .map((s) => s.genotype.sequencing_depth || '-')
                    .join(', ')
            }
        }
        return result
    })
}
