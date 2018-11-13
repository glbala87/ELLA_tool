import { Compute } from 'cerebral'
import getClassification from '../../interpretation/computed/getClassification'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (let alleleId of Object.keys(alleles)) {
            result[alleleId] = get(getClassification(alleles[alleleId]))
        }
        return result
    })
}
