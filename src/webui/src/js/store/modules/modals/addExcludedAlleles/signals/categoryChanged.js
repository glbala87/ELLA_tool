import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'
import getAlleleIdsCategory from '../computed/getAlleleIdsCategory'

export default [
    set(state`modals.addExcludedAlleles.category`, props`category`),
    set(state`modals.addExcludedAlleles.selectedPage`, 1),
    set(state`modals.addExcludedAlleles.categoryAlleleIds`, getAlleleIdsCategory),
    loadExcludedAlleles
]
