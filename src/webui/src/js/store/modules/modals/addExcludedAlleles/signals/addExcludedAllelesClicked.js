import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAlleleIdsByGene from '../actions/getAlleleIdsByGene'
import toast from '../../../../common/factories/toast'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'
import getFilterConfig from '../actions/getFilterConfig'

export default [
    set(state`modals.addExcludedAlleles.analysisId`, props`analysisId`),
    set(state`modals.addExcludedAlleles.genepanel`, props`genepanel`),
    set(state`modals.addExcludedAlleles.excludedAlleleIds`, props`excludedAlleleIds`),
    ({ props }) => {
        // Make copy to avoid changing input props
        return { includedAlleleIds: props.includedAlleleIds.slice() }
    },
    set(state`modals.addExcludedAlleles.includedAlleleIds`, props`includedAlleleIds`),
    getFilterConfig,
    {
        success: [set(state`modals.addExcludedAlleles.filterconfig`, props`result`)],
        error: [toast('error', 'Failed to load filter config')]
    },
    set(state`modals.addExcludedAlleles.readOnly`, props`readOnly`),
    set(state`modals.addExcludedAlleles.category`, 'all'),
    set(state`modals.addExcludedAlleles.itemsPerPage`, 20),
    set(state`modals.addExcludedAlleles.selectedPage`, 1),
    set(state`modals.addExcludedAlleles.show`, true),
    set(state`modals.addExcludedAlleles.categoryAlleleIds`, getAlleleIdsCategory),
    set(props`alleleIds`, state`modals.addExcludedAlleles.categoryAlleleIds`), // Defaults to 'all', so we get all possible allele ids
    getAlleleIdsByGene,
    {
        success: [
            set(state`modals.addExcludedAlleles.data.alleleIdsByGene`, props`result`),
            loadExcludedAlleles,
            // Cannot be parallell since genepanel is loaded in loadExcludedAlleles
            loadIncludedAlleles
        ],
        error: [toast('error', 'Failed to load variants')]
    }
]
