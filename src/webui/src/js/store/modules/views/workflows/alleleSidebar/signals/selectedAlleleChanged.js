import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import updateIgvLocus from '../../visualization/actions/updateIgvLocus'

export default [
    set(state`views.workflows.selectedAllele`, props`alleleId`),
    updateSuggestedClassification,
    updateIgvLocus,
    ({ props }) => {
        console.log(`Selected allele id: ${props.alleleId}`)
    }
]
