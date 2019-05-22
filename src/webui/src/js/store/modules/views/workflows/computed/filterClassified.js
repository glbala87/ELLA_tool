import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getClassification from '../interpretation/computed/getClassification'

export default function(inverse = false, alleles) {
    return Compute(alleles, (alleles, get) => {
        return alleles.filter((allele) => {
            const alleleClassification = get(
                getClassification(allele)
            )
            const isClassifiedAndNotOutdated = alleleClassification.hasClassification && !alleleClassification.outdated
            return inverse ? !isClassifiedAndNotOutdated : isClassifiedAndNotOutdated
        })
    })
}
