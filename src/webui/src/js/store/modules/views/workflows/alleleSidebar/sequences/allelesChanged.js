import { Compute } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareSelectedAllele from '../actions/prepareSelectedAllele'
import sortSections from '../actions/sortSections'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'

export default [
    sortSections,
    prepareSelectedAllele,
    [set(props`alleleId`, state`views.workflows.selectedAllele`), updateSuggestedClassification]
]
