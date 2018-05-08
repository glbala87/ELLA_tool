import { deepCopy } from '../../../../../util'
import { parallel, sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import toastr from '../../../../common/factories/toastr'
import prepareInterpretationState from './prepareInterpretationState'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'

export default sequence('loadAlleles', [
    getAlleles,
    {
        success: [set(state`views.workflows.data.alleles`, props`result`)],
        error: [toastr('error', 'Failed to load variant(s)', 30000)]
    },
    prepareInterpretationState,
    allelesChanged // Update alleleSidebar
])
