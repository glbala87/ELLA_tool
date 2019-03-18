import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'
import getAlleleIdsByGene from '../actions/getAlleleIdsByGene'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import loadIncludedAlleles from '../sequences/loadIncludedAlleles'

export default [
    set(state`views.workflows.modals.addExcludedAlleles.analysisId`, props`analysisId`),
    set(state`views.workflows.modals.addExcludedAlleles.genepanel`, props`genepanel`),
    set(
        state`views.workflows.modals.addExcludedAlleles.excludedAlleleIds`,
        props`excludedAlleleIds`
    ),
    ({ props }) => {
        // Make copy to avoid changing input props
        return { includedAlleleIds: props.includedAlleleIds.slice() }
    },
    set(
        state`views.workflows.modals.addExcludedAlleles.includedAlleleIds`,
        props`includedAlleleIds`
    ),
    set(state`views.workflows.modals.addExcludedAlleles.filterconfig`, props`filterConfig`),
    set(state`views.workflows.modals.addExcludedAlleles.readOnly`, props`readOnly`),
    set(state`views.workflows.modals.addExcludedAlleles.category`, 'all'),
    set(state`views.workflows.modals.addExcludedAlleles.itemsPerPage`, 20),
    set(state`views.workflows.modals.addExcludedAlleles.selectedPage`, 1),
    set(state`views.workflows.modals.addExcludedAlleles.show`, true),
    set(state`views.workflows.modals.addExcludedAlleles.categoryAlleleIds`, getAlleleIdsCategory),
    set(props`alleleIds`, state`views.workflows.modals.addExcludedAlleles.categoryAlleleIds`), // Defaults to 'all', so we get all possible allele ids
    getAlleleIdsByGene,
    {
        success: [
            set(
                state`views.workflows.modals.addExcludedAlleles.data.alleleIdsByGene`,
                props`result`
            ),
            loadExcludedAlleles,
            // Cannot be parallell since genepanel is loaded in loadExcludedAlleles
            loadIncludedAlleles
        ],
        error: [toast('error', 'Failed to load variants')]
    }
]
