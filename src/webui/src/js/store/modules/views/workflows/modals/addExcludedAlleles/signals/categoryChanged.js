import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'

export default [
    set(state`views.workflows.modals.addExcludedAlleles.category`, props`category`),
    set(state`views.workflows.modals.addExcludedAlleles.selectedPage`, 1),
    set(state`views.workflows.modals.addExcludedAlleles.categoryAlleleIds`, getAlleleIdsCategory),
    loadExcludedAlleles
]
