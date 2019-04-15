import { Compute } from 'cerebral'

export default (alleles) => {
    return Compute(alleles, (alleles) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (let [alleleId, allele] of Object.entries(alleles)) {
            const sourcesWithData = []
            if (allele.annotation.external.HGMD) {
                sourcesWithData.push('HGMD')
            }
            if (allele.annotation.external.CLINVAR) {
                sourcesWithData.push('Clinvar')
            }
            result[alleleId] = sourcesWithData
        }
        return result
    })
}
