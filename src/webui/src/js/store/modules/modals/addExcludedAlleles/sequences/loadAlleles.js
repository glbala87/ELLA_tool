import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'
import getAlleleIdsForGene from '../computed/getAlleleIdsForGene'
import getAlleleIdsSlice from '../computed/getAlleleIdsSlice'
import getAlleles from '../actions/getAlleles'
import toast from '../../../../common/factories/toast'

export default sequence('loadAlleles', [
    set(state`modals.addExcludedAlleles.categoryAlleleIds`, getAlleleIdsCategory),
    set(state`modals.addExcludedAlleles.geneAlleleIds`, getAlleleIdsForGene),
    set(state`modals.addExcludedAlleles.viewAlleleIds`, getAlleleIdsSlice),
    set(props`alleleIds`, state`modals.addExcludedAlleles.viewAlleleIds`),
    getAlleles,
    {
        success: [set(state`modals.addExcludedAlleles.data.alleles`, props`result`)],
        error: [toast('error', 'Failed to load variants')]
    }
])
