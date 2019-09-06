import toast from '../../../../../common/factories/toast'
import removeAttachment from '../actions/removeAttachment'
import setDirty from '../actions/setDirty'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'

export default [
    canUpdateAlleleAssessment,
    {
        true: [removeAttachment, setDirty],
        false: [toast('error', 'Could not remove attachment.')]
    }
]
