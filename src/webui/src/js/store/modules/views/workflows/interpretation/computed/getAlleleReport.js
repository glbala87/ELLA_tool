import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

/**
 * Returns EITHER:
 * - If assessment is set to reused: the allele's allelereport
 *   from backend
 * - If not set to reused: the allelereport from state
 */
export default (alleleId) => {
    return Compute(alleleId, getAlleleState(alleleId), (alleleId, alleleState, get) => {
        if (!alleleState) {
            return
        }
        if ('reuse' in alleleState.allelereport && alleleState.allelereport.reuse) {
            return get(state`views.workflows.interpretation.data.alleles.${alleleId}`)
                .allele_assessment
        }
        return alleleState.allelereport
    })
}
