import { props, state } from 'cerebral/tags'
import { when, set } from 'cerebral/operators'
import canUpdateAlleleAssessment from '../../interpretation/operators/canUpdateAlleleAssessment'
import updateSuggestedClassification from '../../interpretation/sequences/updateSuggestedClassification'
import setDirty from '../../interpretation/actions/setDirty'
import changeClassification from '../../interpretation/sequences/changeClassification'
import toast from '../../../../../common/factories/toast'
import addAcmgCode from '../../interpretation/actions/addAcmgCode'
import setVerificationStatus from '../../actions/setVerificationStatus'
import setNotRelevant from '../../actions/setNotRelevant'
import checkAddRemoveAlleleToReport from '../../interpretation/actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../sequences/allelesChanged'
import selectedAlleleChanged from './selectedAlleleChanged'

export default [
    // Select the allele
    set(state`views.workflows.selectedAllele`, props`alleleId`),
    selectedAlleleChanged,

    // Update relevant data
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
                false: [toast('error', 'Could not add ACMG code')]
            }
        ],

        false: []
    },
    when(props`verificationStatus`),
    {
        true: [
            setVerificationStatus,
            ({ props }) => {
                return {
                    checkReportAlleleIds: [props.alleleId]
                }
            },
            checkAddRemoveAlleleToReport,
            allelesChanged
        ],
        false: []
    },
    when(props`notRelevant`),
    {
        true: [
            setNotRelevant,
            ({ props }) => {
                return {
                    checkReportAlleleIds: [props.alleleId]
                }
            },
            checkAddRemoveAlleleToReport,
            allelesChanged
        ],
        false: []
    }
]
