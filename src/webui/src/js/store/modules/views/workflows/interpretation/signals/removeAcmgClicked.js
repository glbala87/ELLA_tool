import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import removeAcmgCode from '../actions/removeAcmgCode'
import setDirty from '../actions/setDirty'
import updateSuggestedClassification from '../sequences/updateSuggestedClassification'

export default [
    canUpdateAlleleAssessment,
    {
        true: [setDirty, removeAcmgCode, updateSuggestedClassification],
        false: [toast('error', 'Could not remove ACMG code')]
    }
]
