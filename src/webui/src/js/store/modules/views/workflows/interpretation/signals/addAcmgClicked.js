import toast from '../../../../../common/factories/toast';
import addAcmgCode from '../actions/addAcmgCode';
import setDirty from '../actions/setDirty';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';
import updateSuggestedClassification from '../sequences/updateSuggestedClassification';

export default [
    canUpdateAlleleAssessment,
    {
        true: [addAcmgCode, updateSuggestedClassification, setDirty],
        false: [toast('error', 'Could not add ACMG code')]
    }
]
