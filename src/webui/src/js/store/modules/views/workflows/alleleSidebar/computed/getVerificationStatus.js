import { Compute } from 'cerebral'
import getVerificationStatus from '../../interpretation/computed/getVerificationStatus'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (const alleleId of Object.keys(alleles)) {
            result[alleleId] = get(getVerificationStatus(alleleId))
        }
        return result
    })
}
