import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

/*
    Returns array of unique consequences, sorted by worse consequences first,
    per id for all transcripts *in the genepanel*.
    This is in other words different than the other worse consequence warnings.
*/
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
            const allConsequences = allele.annotation.filtered.reduce((acc, cur) => {
                return acc.concat(cur.consequences)
            }, [])
            if (allConsequences.length) {
                const uniqueConsequences = [...new Set(allConsequences)]
                result[alleleId] = uniqueConsequences
                    .sort(sortFunc)
                    .map((c) => c.replace('_variant', ''))
                    .join(', ')
            } else {
                result[alleleId] = ''
            }
        }
        return result
    })
}
