import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import upgradeDowngradeAcmgCode from '../actions/upgradeDowngradeAcmgCode'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, upgradeDowngradeAcmgCode],
        false: [toast('error', 'Could not add ACMG code')]
    }
]
