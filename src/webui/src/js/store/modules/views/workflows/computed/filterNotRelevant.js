import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default function(inverse = false, alleles) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.selected`,
        (alleles, interpretation) => {
            return alleles.filter((allele) => {
                const notRelevant = Boolean(
                    interpretation.state.allele[allele.id].analysis.notrelevant
                )
                return inverse ? !notRelevant : notRelevant
            })
        }
    )
}
