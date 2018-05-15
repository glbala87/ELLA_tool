import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'
import getAlleleIdsForGene from '../computed/getAlleleIdsForGene'
import getAlleleIdsSlice from '../computed/getAlleleIdsSlice'
import getAlleles from '../actions/getAlleles'
import toastr from '../../../../common/factories/toastr'

export default sequence('loadIncludedAlleles', [
    set(props`alleleIds`, state`modals.addExcludedAlleles.includedAlleleIds`),
    getAlleles,
    {
        success: [set(state`modals.addExcludedAlleles.data.includedAlleles`, props`result`)],
        error: [toastr('error', 'Failed to load included variants')]
    }
])
