import { props, state } from 'cerebral/tags'
import { when, set } from 'cerebral/operators'
import changeClassification from '../../interpretation/sequences/changeClassification'
import selectedAlleleChanged from '../../sequences/selectedAlleleChanged'
import setVerificationStatus from '../../sequences/setVerificationStatus'
import setNotRelevant from '../../sequences/setNotRelevant'
import canUpdateAlleleAssessment from '../../interpretation/operators/canUpdateAlleleAssessment'
import setDirty from '../../interpretation/actions/setDirty'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import addAcmgCode from '../../interpretation/actions/addAcmgCode'

export default [
    // Select the allele
    set(state`views.workflows.selectedAllele`, props`alleleId`),
    selectedAlleleChanged,

    // Update relevant data
    when(props`code`),
    {
        true: [
            canUpdateAlleleAssessment,
            {
                true: [addAcmgCode, setDirty, updateSuggestedClassification],
                false: []
            }
        ],
        false: []
    },
    when(props`classification`),
    {
        true: changeClassification,
        false: []
    },
    when(props`verificationStatus`),
    {
        true: setVerificationStatus,
        false: []
    },
    when(props`notRelevant`),
    {
        true: setNotRelevant,
        false: []
    }
]
