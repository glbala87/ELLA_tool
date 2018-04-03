import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../actions/prepareSelectedAllele'
import sortSections from '../actions/sortSections'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'

export default [
    sortSections,
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
