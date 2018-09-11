import { set, debounce } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadAlleles from '../sequences/loadAlleles'

export default [
    debounce(300),
    {
        continue: [
            set(state`modals.addExcludedAlleles.selectedPage`, props`selectedPage`),
            loadAlleles
        ],
        discard: []
    }
]
