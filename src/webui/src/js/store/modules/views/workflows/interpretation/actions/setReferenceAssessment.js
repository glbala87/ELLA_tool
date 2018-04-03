import getAlleleState from '../computed/getAlleleState'

/**
 * Sets new referenceassessment data into alleleState.
 * Logic is as follows:
 * - If an existing, non-reused referenceassessment exists, update inplace
 * - If existing, _reused_ referenceassessment exists, remove reuse status and update
 * - If neither, add a new one
 */
export default function setReferenceAssessment({ state, resolve, props }) {
    if (!('evaluation' in props)) {
        throw Error("Missing required props 'evaluation'")
    }

    const alleleId = props.alleleId
    const referenceId = props.referenceId
    const alleleState = resolve.value(getAlleleState(props.alleleId))

    const raIdx = alleleState.referenceassessments.findIndex((ra) => {
        return ra.reference_id === referenceId && ra.allele_id === alleleId
    })

    const newReferenceAssessment = {
        evaluation: props.evaluation,
        allele_id: alleleId,
        reference_id: referenceId
    }

    if (raIdx >= 0) {
        // We have a match, overwrite existing (also clear reuse status if present)
        let existing = state.get(
            `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}`
        )
        existing = Object.assign({}, existing, newReferenceAssessment)
        if ('reuse' in existing) {
            existing.reuse = false
            delete existing.id
        }
        state.set(
            `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments.${raIdx}`,
            existing
        )
    } else {
        // Insert new entry
        state.push(
            `views.workflows.interpretation.selected.state.allele.${alleleId}.referenceassessments`,
            newReferenceAssessment
        )
    }
}
