import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadAlleles from '../sequences/loadAlleles'

export default [
    set(state`modals.addExcludedAlleles.category`, props`category`),
    set(state`modals.addExcludedAlleles.selectedPage`, 1),
    loadAlleles
]
