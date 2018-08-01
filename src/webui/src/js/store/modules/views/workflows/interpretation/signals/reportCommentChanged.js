import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleReport from '../operators/canUpdateAlleleReport'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'

export default [
    debounce(200),
    {
        continue: [setDirty, set(module`selected.state.report.comment`, props`comment`)],
        discard: []
    }
]
