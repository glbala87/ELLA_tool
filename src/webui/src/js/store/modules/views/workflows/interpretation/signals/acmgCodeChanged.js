import { debounce, when } from 'cerebral/operators';
import { props } from 'cerebral/tags';
import toast from '../../../../../common/factories/toast';
import acmgCodeChanged from '../actions/acmgCodeChanged';
import setDirty from '../actions/setDirty';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';
import updateSuggestedClassification from '../sequences/updateSuggestedClassification';


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
