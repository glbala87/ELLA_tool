import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function(allele) {
    return Compute(allele, state`views.workflows.selectedAllele`, (allele, selectedAllele) => {
        if (!selectedAllele || !allele) {
            return false
        }
        return selectedAllele === allele.id
    })
}
