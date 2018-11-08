import { Compute } from 'cerebral'
import getAlleleState from './getAlleleState'

export default (alleleId) => {
    return Compute(alleleId, (alleleId, get) => {
        if (!alleleId) {
            return null
        }

        const alleleState = get(getAlleleState(alleleId))
        return alleleState ? alleleState.analysis.notrelevant : null
    })
}
