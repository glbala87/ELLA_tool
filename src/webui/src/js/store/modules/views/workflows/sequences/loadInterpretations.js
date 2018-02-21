import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getInterpretations from '../actions/getInterpretations'
import prepareSelectedInterpretation from '../actions/prepareSelectedInterpretation'
import prepareInterpretationState from '../actions/prepareInterpretationState'
import prepareStartMode from '../actions/prepareStartMode'
import loadInterpretationData from '../signals/loadInterpretationData'

import toastr from '../../../../common/factories/toastr'

export default sequence('LoadInterpretations', [
    set(state`views.workflows.loaded`, false),
    getInterpretations,
    {
        error: [toastr('error', 'Failed to load interpretations', 30000)],
        success: [
            set(state`views.workflows.data.interpretations`, props`result`),
            prepareSelectedInterpretation,
            prepareStartMode,
            loadInterpretationData,
            set(state`views.workflows.loaded`, true)
        ]
    }
])
