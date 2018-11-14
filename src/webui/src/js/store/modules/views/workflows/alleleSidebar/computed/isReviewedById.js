import { Compute } from 'cerebral'
import getAlleleState from '../../interpretation/computed/getAlleleState'

export default (alleles) => {
    return Compute(alleles, (alleles, get) => {
        const result = {}
        if (!alleles) {
            return result
        }

        for (const alleleId of Object.keys(alleles)) {
            const alleleState = get(getAlleleState(alleleId))
            result[alleleId] =
                alleleState && alleleState.workflow ? alleleState.workflow.reviewed : null
        }
        return result
    })
}
