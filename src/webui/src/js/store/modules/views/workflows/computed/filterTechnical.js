import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default function(inverse = false, alleles) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.state.allele`,
        (alleles, alleleStates) => {
            return alleles.filter((allele) => {
                const technical = Boolean(
                    alleleStates[allele.id].analysis.verification === 'technical'
                )
                return inverse ? !technical : technical
            })
        }
    )
}
