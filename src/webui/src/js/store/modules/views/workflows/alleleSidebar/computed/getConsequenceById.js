import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (alleles) => {
    return Compute(alleles, state`app.config`, (alleles, config) => {
        const result = {}
        if (!alleles) {
            return result
        }
        const consequencePriority = config.transcripts.consequences
        const sortFunc = (a, b) => {
            return consequencePriority.indexOf(a) - consequencePriority.indexOf(b)
        }
        for (let [alleleId, allele] of Object.entries(alleles)) {
            result[alleleId] = allele.annotation.filtered
                .map((t) => t.consequences.sort(sortFunc).map((c) => c.replace('_variant', '')))
                .join(' | ')
        }
        return result
    })
}
