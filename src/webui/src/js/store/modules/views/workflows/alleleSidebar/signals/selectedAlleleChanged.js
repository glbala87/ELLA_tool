import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'

export default [
    set(state`views.workflows.selectedAllele`, props`alleleId`),
    updateSuggestedClassification
]
