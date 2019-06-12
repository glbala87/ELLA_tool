import { props, state } from 'cerebral/tags'
import { when, set } from 'cerebral/operators'
import changeClassification from '../../interpretation/sequences/changeClassification'
import selectedAlleleChanged from '../../sequences/selectedAlleleChanged'
import setVerificationStatus from '../../sequences/setVerificationStatus'
import setNotRelevant from '../../sequences/setNotRelevant'
import toggleAcmgCode from '../sequences/toggleAcmgCode'

export default [
    // Select the allele
    when(props`selectAllele`),
    {
        true: [set(state`views.workflows.selectedAllele`, props`alleleId`), selectedAlleleChanged],
        false: []
    },
    // Update relevant data
    when(props`code`),
    {
        true: [toggleAcmgCode],
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
