import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'

export default [
    set(state`views.workflows.modals.addExcludedAlleles.selectedGene`, props`gene`),
    set(state`views.workflows.modals.addExcludedAlleles.selectedPage`, 1),
    loadExcludedAlleles
]
