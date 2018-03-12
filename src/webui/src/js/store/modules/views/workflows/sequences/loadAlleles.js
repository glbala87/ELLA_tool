import { deepCopy } from '../../../../../util'
import { parallel, sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import hasInterpretations from '../actions/hasInterpretations'
import getAcmgCodes from '../actions/getAcmgCodes'
import prepareSuggestedAcmg from '../actions/prepareSuggestedAcmg'
import prepareInterpretationState from '../actions/prepareInterpretationState'
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'

import toastr from '../../../../common/factories/toastr'
import autoReuseExistingAlleleassessments from '../interpretation/actions/autoReuseExistingAlleleassessments'
import autoReuseExistingReferenceAssessments from '../interpretation/actions/autoReuseExistingReferenceAssessments'

export default sequence('loadAlleles', [
    // If there are no interpretations (can happen when type: 'allele'),
    // we need to reuse allele loaded initially
    hasInterpretations,
    {
        true: [
            getAlleles,
            {
                success: [set(state`views.workflows.data.alleles`, props`result`)],
                error: [toastr('error', 'Failed to load variant(s)', 30000)]
            }
        ],
        false: [
            ({ props, state }) => {
                const allele = deepCopy(state.get('views.workflows.allele'))
                return { alleleResult: { [allele.id]: allele } }
            }
        ]
    },
    prepareInterpretationState,
    // Prepare props for checkAddRemoveAlleleToReport
    ({ state }) => {
        return { alleleIds: Object.keys(state.get('views.workflows.data.alleles')) }
    },
    checkAddRemoveAlleleToReport,
    autoReuseExistingAlleleassessments,
    autoReuseExistingReferenceAssessments,
    allelesChanged // Update alleleSidebar
])
