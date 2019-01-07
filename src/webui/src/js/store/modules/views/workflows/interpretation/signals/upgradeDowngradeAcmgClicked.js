import toast from '../../../../../common/factories/toast';
import setDirty from '../actions/setDirty';
import upgradeDowngradeAcmgCode from '../actions/upgradeDowngradeAcmgCode';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, upgradeDowngradeAcmgCode],
        false: [toast('error', 'Could not add ACMG code')]
    }
]
