import { when, push, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'
import removeAttachment from '../actions/removeAttachment'

export default [
    canUpdateAlleleAssessment,
    {
        true: [removeAttachment, setDirty],
        false: [toast('error', 'Could not remove attachment.')]
    }
]
