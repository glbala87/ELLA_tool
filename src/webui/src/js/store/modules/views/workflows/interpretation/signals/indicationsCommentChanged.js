import { set, debounce } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import setDirty from '../actions/setDirty'

export default [
    debounce(200),
    {
        continue: [setDirty, set(module`selected.state.report.indicationscomment`, props`comment`)],
        discard: []
    }
]
