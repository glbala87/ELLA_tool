import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default function(inverse = false, alleles) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.selected`,
        (alleles, interpretation) => {
            return alleles.filter((allele) => {
                const technical = Boolean(
                    interpretation.state.allele[allele.id].verification === 'technical'
                )
                return inverse ? !technical : technical
            })
        }
    )
}
