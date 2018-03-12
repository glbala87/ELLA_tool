import getClassification from '../computed/getClassification'
import getAlleleState from '../computed/getAlleleState'

export default function checkAddRemoveAlleleToReport({ props, state, resolve }) {
    const { alleleIds } = props
    const config = state.get('app.config')

    for (let alleleId of alleleIds) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        const classification = resolve.value(getClassification(alleleId))
        const configOption = config.classification.options.find(o => {
            return o.value === classification
        })
        if (
            configOption &&
            configOption.include_report &&
            alleleState.verification !== 'technical'
        ) {
            state.set(
                `views.workflows.interpretation.selected.state.allele.${alleleId}.report.included`,
                true
            )
        } else {
            state.set(
                `views.workflows.interpretation.selected.state.allele.${alleleId}.report.included`,
                false
            )
        }
    }
}
