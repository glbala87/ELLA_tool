import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

/**
 * Returns EITHER:
 * - If assessment is set to reused: the allele's referenceassessment
 *   from backend
 * - If not set to reused: the referenceassessment from state
 */
export default (alleleId, referenceId) => {
    return Compute(
        alleleId,
        referenceId,
        getAlleleState(alleleId),
        (alleleId, referenceId, alleleState, get) => {
            if (!alleleId) {
                return
            }
            const allele = get(state`views.workflows.data.alleles.${alleleId}`)
            const referenceAssessment = alleleState.referenceassessments.find(ra => {
                return ra.reference_id === referenceId && ra.allele_id === alleleId
            })
            if (referenceAssessment && referenceAssessment.reuse) {
                return allele.reference_assessments.find(ra => {
                    return ra.reference_id === referenceId && ra.allele_id === alleleId
                })
            }
            return referenceAssessment // Can be undefined
        }
    )
}
