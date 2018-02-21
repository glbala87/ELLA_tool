import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import removeAcmgCode from '../actions/removeAcmgCode'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, removeAcmgCode],
        false: [toastr('error', 'Could not remove ACMG code')]
    }
]
