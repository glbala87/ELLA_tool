import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getClassification from '../interpretation/computed/getClassification'

export default function(inverse = false, alleles) {
    return Compute(alleles, (alleles, get) => {
        return alleles.filter((allele) => {
            const hasValidClassification = get(
                getClassification(allele)
            ).hasValidClassification
            return inverse ? !hasValidClassification : hasValidClassification
        })
    })
}
