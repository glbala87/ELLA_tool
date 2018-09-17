import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import sortSections from '../actions/sortSections'
import prepareSelectedAllele from '../actions/prepareSelectedAllele'
import updateIgvLocus from '../../visualization/actions/updateIgvLocus'

export default [
    sortSections,
    prepareSelectedAllele,
    when(state`views.workflows.selectedAllele`),
    {
        true: [set(props`alleleId`, state`views.workflows.selectedAllele`), updateIgvLocus],
        false: []
    }
]
