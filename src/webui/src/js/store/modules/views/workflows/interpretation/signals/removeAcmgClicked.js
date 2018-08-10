import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import removeAcmgCode from '../actions/removeAcmgCode'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, removeAcmgCode],
        false: [toast('error', 'Could not remove ACMG code')]
    }
]
