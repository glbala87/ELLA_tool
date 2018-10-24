import { set, toggle, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import setDirty from '../../interpretation/actions/setDirty'
import getClassification from '../../interpretation/computed/getClassification'
import selectedAlleleChanged from './selectedAlleleChanged'

function canAddToReport({ state, props, path, resolve }) {
    const { alleleId } = props
    const verificationStatus = state.get(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.verification`
    )
    const classification = resolve.value(getClassification(alleleId))
    if (verificationStatus !== 'technical' && classification) {
        return path.true()
    }
    return path.false()
}

export default [
    equals(state`views.workflows.selectedComponent`),
    {
        Report: [
            canAddToReport,
            {
                true: [
                    setDirty,
                    toggle(
                        state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.report.included`
                    )
                ],
                false: [] // no op
            }
        ],
        Classification: [
            set(state`views.workflows.selectedAllele`, props`alleleId`),
            ({ props }) => {
                console.log(`Selected allele id: ${props.alleleId}`)
            },
            selectedAlleleChanged
        ],
        Visualization: [
            set(state`views.workflows.selectedAllele`, props`alleleId`),
            ({ props }) => {
                console.log(`Selected allele id: ${props.alleleId}`)
            },
            selectedAlleleChanged
        ],
        default: []
    }
]
