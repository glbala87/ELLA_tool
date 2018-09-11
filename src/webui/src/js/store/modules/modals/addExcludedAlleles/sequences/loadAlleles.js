import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleleIdsForGene from '../computed/getAlleleIdsForGene'
import getAlleleIdsSlice from '../computed/getAlleleIdsSlice'
import getAlleles from '../actions/getAlleles'
import toast from '../../../../common/factories/toast'
import progress from '../../../../common/factories/progress'

export default sequence('loadAlleles', [
    progress('start'),
    progress('set', 70),
    set(state`modals.addExcludedAlleles.geneAlleleIds`, getAlleleIdsForGene),
    set(state`modals.addExcludedAlleles.viewAlleleIds`, getAlleleIdsSlice),
    set(props`alleleIds`, state`modals.addExcludedAlleles.viewAlleleIds`),
    getAlleles,
    {
        success: [set(state`modals.addExcludedAlleles.data.alleles`, props`result`)],
        error: [toast('error', 'Failed to load variants')]
    },
    progress('done')
])
