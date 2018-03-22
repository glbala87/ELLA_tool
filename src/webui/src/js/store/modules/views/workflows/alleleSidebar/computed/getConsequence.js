import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default Compute(
    state`views.workflows.data.alleles`,
    state`app.config`,
    (alleles, config) => {
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
                .map(t => t.consequences.sort(sortFunc)[0].replace('_variant', ''))
                .join(' | ')
        }
        return result
    }
)
