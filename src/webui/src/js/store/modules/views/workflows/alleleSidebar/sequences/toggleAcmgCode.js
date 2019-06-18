import { when } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../../interpretation/operators/canUpdateAlleleAssessment'
import addAcmgCode from '../../interpretation/actions/addAcmgCode'
import setDirty from '../../interpretation/actions/setDirty'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import removeAcmgCode from '../../interpretation/actions/removeAcmgCode'

export default [
    canUpdateAlleleAssessment,
    {
        true: [
            // If provided code has uuid, it must have been added
            // already. If so, remove it
            when(props`code.uuid`),
            {
                true: [removeAcmgCode],
                false: [addAcmgCode]
            },
            setDirty,
            updateSuggestedClassification
        ],
        false: []
    }
]
