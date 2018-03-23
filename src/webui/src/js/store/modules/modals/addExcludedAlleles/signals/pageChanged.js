import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadAlleles from '../sequences/loadAlleles'

export default [
    set(state`modals.addExcludedAlleles.selectedPage`, props`selectedPage`),
    loadAlleles
]
