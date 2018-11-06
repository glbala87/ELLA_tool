import getClassification from '../computed/getClassification'
import getAlleleState from '../computed/getAlleleState'

export default function checkAddRemoveAlleleToReport({ props, state, resolve }) {
    const { checkReportAlleleIds } = props
    const alleles = state.get('views.workflows.data.alleles')
    const config = state.get('app.config')

    for (let alleleId of checkReportAlleleIds) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        const classification = resolve.value(getClassification(alleles[alleleId]))
        const configOption = config.classification.options.find((o) => {
            return o.value === classification.classification
        })
        if (
            configOption &&
            configOption.include_report &&
            alleleState.analysis.verification !== 'technical' &&
            !alleleState.analysis.notrelevant
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
