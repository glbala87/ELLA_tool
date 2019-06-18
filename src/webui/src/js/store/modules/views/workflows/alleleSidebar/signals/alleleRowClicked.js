import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import selectedAlleleChanged from '../../sequences/selectedAlleleChanged'

function canAddToReport({ state, props, path, resolve }) {
    const { alleleId } = props
    const verificationStatus = state.get(
        `views.workflows.interpretation.state.allele.${alleleId}.analysis.verification`
    )
    const allele = state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
    const classification = resolve.value(getClassification(allele))
    if (verificationStatus !== 'technical' && classification.hasValidClassification) {
        return path.true()
    }
    return path.false()
}

export default [
    equals(state`views.workflows.selectedComponent`),
    {
        Classification: [
            set(state`views.workflows.selectedAllele`, props`alleleId`),
            ({ props }) => {
                console.log(`Selected allele id: ${props.alleleId}`)
            },
            selectedAlleleChanged
        ],
        otherwise: []
    }
]
