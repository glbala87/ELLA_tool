import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import acmgCodeChanged from '../actions/acmgCodeChanged'
import setDirty from '../actions/setDirty'
import updateSuggestedClassification from '../sequences/updateSuggestedClassification'

export default [
    canUpdateAlleleAssessment,
    {
        true: [acmgCodeChanged, updateSuggestedClassification, setDirty],
        false: [toastr('error', 'Could not change ACMG code')]
    }
]
