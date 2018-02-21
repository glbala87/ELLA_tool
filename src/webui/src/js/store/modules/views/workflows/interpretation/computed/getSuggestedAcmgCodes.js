import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

export default alleleId => {
    return Compute(alleleId, getAlleleState(alleleId), (alleleId, alleleState, get) => {
        if (!alleleState) {
            return []
        }
        return alleleState.alleleassessment.evaluation.acmg.suggested.filter(
            c => !c.code.startsWith('REQ')
        )
    })
}
