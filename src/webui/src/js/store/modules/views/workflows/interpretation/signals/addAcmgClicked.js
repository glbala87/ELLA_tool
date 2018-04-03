import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import addAcmgCode from '../actions/addAcmgCode'
import setDirty from '../actions/setDirty'
import updateSuggestedClassification from '../sequences/updateSuggestedClassification'

export default [
    canUpdateAlleleAssessment,
    {
        true: [addAcmgCode, updateSuggestedClassification, setDirty],
        false: [toastr('error', 'Could not add ACMG code')]
    }
]
