import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAlleleIdsForGene from '../computed/getAlleleIdsForGene'
import getAlleleIdsSlice from '../computed/getAlleleIdsSlice'
import getAlleles from '../actions/getAlleles'
import toast from '../../../../common/factories/toast'
import progress from '../../../../common/factories/progress'
import getGenepanel from '../actions/getGenepanel'

export default sequence('loadExcludedAlleles', [
    progress('start'),
    progress('set', 70),
    set(state`modals.addExcludedAlleles.geneAlleleIds`, getAlleleIdsForGene),
    set(state`modals.addExcludedAlleles.viewAlleleIds`, getAlleleIdsSlice),
    getGenepanel,
    {
        success: [
            set(state`modals.addExcludedAlleles.data.genepanel`, props`result`),
            set(props`alleleIds`, state`modals.addExcludedAlleles.viewAlleleIds`),
            getAlleles,
            {
                success: [set(state`modals.addExcludedAlleles.data.alleles`, props`result`)],
                error: [toast('error', 'Failed to load variants')]
            }
        ],
        error: [toast('error', 'Failed to load genepanel')]
    },
    progress('done')
])
