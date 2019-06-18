import { deepCopy } from '../../../../../../util'
import getAlleleState from '../computed/getAlleleState'
import getReferenceAssessment from '../computed/getReferenceAssessment'

/**
 * Sets new referenceassessment data into alleleState.
 * Logic is as follows:
 * - If existing, update inplace and set reuse to false
 * - If not existing, add a new one
 */
export default function setReferenceAssessment({ state, resolve, props }) {
    if (!('evaluation' in props) && !('comment' in props)) {
        throw Error("Missing required props 'evaluation' or 'comment'")
    }

    const alleleId = props.alleleId
    const referenceId = props.referenceId
    const alleleState = resolve.value(getAlleleState(props.alleleId))

    const raIdx = alleleState.referenceassessments.findIndex((ra) => {
        return ra.reference_id === referenceId && ra.allele_id === alleleId
    })

    const newReferenceAssessment = {
        allele_id: alleleId,
        reference_id: referenceId,
        evaluation: props.evaluation || {}
    }

    if (raIdx >= 0) {
        // Match on existing one (either reused or not)
        // Clear reuse status if present
        let existingInState = state.get(
            `views.workflows.interpretation.state.allele.${alleleId}.referenceassessments.${raIdx}`
        )
        existingInState = Object.assign({}, existingInState, newReferenceAssessment)
        if ('reuse' in existingInState) {
            existingInState.reuse = false
            delete existingInState.id
        }
        // If there's no evaluation in props, we need to copy from whatever is there already
        // either from backend data or in state
        if (!props.evaluation) {
            const existingReferenceAssessment = resolve.value(
                getReferenceAssessment(alleleId, referenceId)
            )
            // deepCopy evaluation in case it's from backend data
            existingInState.evaluation = deepCopy(existingReferenceAssessment.evaluation)
        }
        if (props.comment) {
            existingInState.evaluation.comment = props.comment
        }
        state.set(
            `views.workflows.interpretation.state.allele.${alleleId}.referenceassessments.${raIdx}`,
            existingInState
        )
    } else {
        // Insert new entry
        if (!props.evaluation) {
            throw new Error(
                "Props 'evaluation' must be defined when creating new reference assessment"
            )
        }

        state.push(
            `views.workflows.interpretation.state.allele.${alleleId}.referenceassessments`,
            newReferenceAssessment
        )
    }
}
