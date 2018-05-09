import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'
import { prepareAlleleAssessmentModel } from '../../../../../common/helpers/alleleState'

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
        let alleleAssessment
        if (alleleState.alleleassessment.reuse) {
            alleleAssessment = get(
                state`views.workflows.data.alleles.${alleleId}.allele_assessment`
            )
        } else {
            alleleAssessment = alleleState.alleleassessment
        }
        // Existing alleleassessment's model might need migrations
        // alleleAssessment can be undefined while state is being modified
        if (alleleAssessment) {
            prepareAlleleAssessmentModel(alleleAssessment)
        }
        return alleleAssessment
    })
}
