import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import acmgCodeChanged from '../actions/acmgCodeChanged'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [acmgCodeChanged, setDirty],
        false: [toastr('error', 'Could not change ACMG code')]
    }
]
