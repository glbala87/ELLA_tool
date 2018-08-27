import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'
import updateSuggestedClassification from '../interpretation/sequences/updateSuggestedClassification'

export default [
    set(state`views.workflows.selectedComponent`, props`selectedComponent`),
    prepareSelectedAllele,
    when(state`views.workflows.selectedAllele`),
    {
        true: [
            set(props`alleleId`, state`views.workflows.selectedAllele`),
            updateSuggestedClassification
        ],
        false: []
    }
]
