import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import upgradeDowngradeAcmgCode from '../actions/upgradeDowngradeAcmgCode'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, upgradeDowngradeAcmgCode],
        false: [toastr('error', 'Could not add ACMG code')]
    }
]
