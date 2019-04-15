import { set, debounce } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadExcludedAlleles from '../sequences/loadExcludedAlleles'

export default [
    debounce(300),
    {
        continue: [
            set(state`views.workflows.modals.addExcludedAlleles.selectedPage`, props`selectedPage`),
            loadExcludedAlleles
        ],
        discard: []
    }
]
