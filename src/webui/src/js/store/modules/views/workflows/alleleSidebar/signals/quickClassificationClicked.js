import { props } from 'cerebral/tags'
import { when } from 'cerebral/operators'
import canUpdateAlleleAssessment from '../../interpretation/operators/canUpdateAlleleAssessment'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import setDirty from '../../interpretation/actions/setDirty'
import changeClassification from '../../interpretation/sequences/changeClassification'
import toastr from '../../../../../common/factories/toastr'
import addAcmgCode from '../../interpretation/actions/addAcmgCode'

export default [
    when(props`classification`),
    {
        true: changeClassification,
        false: []
    },
    when(props`code`),
    {
        true: [
            canUpdateAlleleAssessment,
            {
                true: [addAcmgCode, updateSuggestedClassification, setDirty],
                false: [toastr('error', 'Could not add ACMG code')]
            }
        ],

        false: []
    }
]
