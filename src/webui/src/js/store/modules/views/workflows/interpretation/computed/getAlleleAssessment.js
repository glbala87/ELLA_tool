import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

/**
 * Returns EITHER:
 * - If assessment is set to reused: the allele's alleleassessment
 *   from backend
 * - If not set to reused: the alleleassessment from state
 */
export default (alleleId) => {
    return Compute(alleleId, getAlleleState(alleleId), (alleleId, alleleState, get) => {
        if (!alleleState) {
            return
        }
        if ('reuse' in alleleState.alleleassessment && alleleState.alleleassessment.reuse) {
            return get(state`views.workflows.data.alleles.${alleleId}`).allele_assessment
        }
        return alleleState.alleleassessment
    })
}
