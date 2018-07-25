import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import toastr from '../../../../common/factories/toastr'
import prepareInterpretationState from './prepareInterpretationState'
import allelesChanged from '../alleleSidebar/sequences/allelesChanged'

export default sequence('loadAlleles', [
    getAlleles,
    {
        success: [
            set(state`views.workflows.data.alleles`, props`result`),
            prepareInterpretationState,
            allelesChanged // Update alleleSidebar
        ],
        error: [toastr('error', 'Failed to load variant(s)', 30000)]
    }
])
