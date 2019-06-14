import toast from '../../../../../common/factories/toast'
import addAcmgCode from '../actions/addAcmgCode'
import setDirty from '../actions/setDirty'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import updateSuggestedClassification from '../sequences/updateSuggestedClassification'
import isAcmgCodeAdded from '../operators/isAcmgCodeAdded'

export default [
    canUpdateAlleleAssessment,
    {
        true: [
            isAcmgCodeAdded,
            {
                true: [toast('info', 'ACMG criterion is already added', 3000)],
                false: [addAcmgCode, updateSuggestedClassification, setDirty]
            }
        ],
        false: []
    }
]
