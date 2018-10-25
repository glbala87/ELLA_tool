import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'

export default [
    set(state`modals.addExcludedAlleles.selectedGene`, props`gene`),
    set(state`modals.addExcludedAlleles.selectedPage`, 1),
    loadExcludedAlleles
]
