import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'
import isAlleleAssessmentReused from './isAlleleAssessmentReused'

/**
 * Returns EITHER:
 * - If assessment is set to reused: the allele's referenceassessment
 *   from backend
 * - If not set to reused: the referenceassessment from state or undefined
 */
export default (alleleId, referenceId) => {
    return Compute(
        alleleId,
        referenceId,
        isAlleleAssessmentReused(alleleId),
        getAlleleState(alleleId),
        (alleleId, referenceId, alleleAssessmentReused, alleleState, get) => {
            if (!alleleId || !referenceId || !alleleState) {
                return
            }
            const allele = get(state`views.workflows.interpretation.data.alleles.${alleleId}`)
            const referenceAssessment = alleleState.referenceassessments.find((ra) => {
                return ra.reference_id === referenceId && ra.allele_id === alleleId
            })
            if (referenceAssessment && referenceAssessment.reuse) {
                return allele.reference_assessments.find((ra) => {
                    return ra.reference_id === referenceId && ra.allele_id === alleleId
                })
            }
            // If alleleAssessment is reused, while the referenceAssessment in alleleState is not reused -> return no data
            // Otherwise the user will see whatever he entered into the state while he reopened the alleleassessment, then reused it
            if (referenceAssessment && alleleAssessmentReused) {
                return null
            }
            return referenceAssessment // Can be undefined
        }
    )
}
