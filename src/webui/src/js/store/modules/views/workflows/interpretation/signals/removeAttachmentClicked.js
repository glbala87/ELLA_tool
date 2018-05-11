import { when, push, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import setDirty from '../actions/setDirty'
import removeAttachment from '../actions/removeAttachment'

export default [
    canUpdateAlleleAssessment,
    {
        true: [removeAttachment, setDirty],
        false: [toastr('error', 'Could not remove attachment.')]
    }
]
