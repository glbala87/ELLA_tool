import { Compute } from 'cerebral'

export default function(allele) {
    return Compute(allele, (allele) => {
        if (!allele) {
            return
        }
        return allele.allele_assessment
    })
}
