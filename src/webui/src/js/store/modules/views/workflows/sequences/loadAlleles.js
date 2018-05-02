import { deepCopy } from '../../../../../util'
import { parallel, sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import getAcmgCodes from '../actions/getAcmgCodes'
import prepareSuggestedAcmg from '../actions/prepareSuggestedAcmg'
import prepareInterpretationState from '../actions/prepareInterpretationState'
import checkAddRemoveAlleleToReport from '../interpretation/actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'
import toastr from '../../../../common/factories/toastr'
import autoReuseExistingAlleleassessments from '../interpretation/actions/autoReuseExistingAlleleassessments'
import autoReuseExistingReferenceAssessments from '../interpretation/actions/autoReuseExistingReferenceAssessments'
import processAlleles from '../../../../common/helpers/processAlleles'

export default sequence('loadAlleles', [
    getAlleles,
    {
        success: [set(state`views.workflows.data.alleles`, props`result`)],
        error: [toastr('error', 'Failed to load variant(s)', 30000)]
    },
    prepareInterpretationState,
    autoReuseExistingAlleleassessments,
    autoReuseExistingReferenceAssessments,
    checkAddRemoveAlleleToReport,
    allelesChanged // Update alleleSidebar
])
