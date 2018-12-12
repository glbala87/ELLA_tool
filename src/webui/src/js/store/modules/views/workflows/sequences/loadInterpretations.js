import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getInterpretations from '../actions/getInterpretations'
import prepareSelectedInterpretation from '../actions/prepareSelectedInterpretation'
import prepareStartMode from '../actions/prepareStartMode'
import loadInterpretationData from '../signals/loadInterpretationData'

import toast from '../../../../common/factories/toast'
import updateLoadingPhase from '../factories/updateLoadingPhase'

export default sequence('loadInterpretations', [
    updateLoadingPhase('start'),
    set(state`views.workflows.loaded`, false),
    updateLoadingPhase('filtering'),
    getInterpretations,
    {
        error: [toast('error', 'Failed to load interpretations', 30000)],
        success: [
            set(state`views.workflows.data.interpretations`, props`result`),
            prepareSelectedInterpretation,
            prepareStartMode,
            updateLoadingPhase('variants'),
            loadInterpretationData,
            updateLoadingPhase('done'),
            set(state`views.workflows.loaded`, true)
        ]
    }
])
