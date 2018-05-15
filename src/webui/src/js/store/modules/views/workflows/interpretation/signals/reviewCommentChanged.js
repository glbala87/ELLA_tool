import { when, set, debounce } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../actions/setDirty'

export default [
    when(state`views.workflows.interpretation.isOngoing`),
    {
        true: [
            setDirty,
            set(
                state`views.workflows.interpretation.selected.state.review_comment`,
                props`reviewComment`
            )
        ],
        false: []
    }
]
