import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default function(inverse = false, alleles) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.state.allele`,
        (alleles, alleleStates) => {
            return alleles.filter((allele) => {
                const notRelevant = Boolean(alleleStates[allele.id].analysis.notrelevant)
                return inverse ? !notRelevant : notRelevant
            })
        }
    )
}
