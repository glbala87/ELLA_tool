import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import acmgCodeChanged from '../actions/acmgCodeChanged'
import setDirty from '../actions/setDirty'
import updateSuggestedClassification from '../sequences/updateSuggestedClassification'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleAssessment,
            {
                true: [
                    acmgCodeChanged,
                    setDirty,
                    when(props`codeChanged`),
                    {
                        true: [updateSuggestedClassification],
                        false: []
                    }
                ],
                false: [toast('error', 'Could not change ACMG code')]
            }
        ],
        discard: []
    }
]
