import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function(allele) {
    return Compute(allele, allele => {
        if (!allele) {
            return
        }
        return allele.allele_assessment
    })
}
