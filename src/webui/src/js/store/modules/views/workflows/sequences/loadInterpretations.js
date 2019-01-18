import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getInterpretations from '../actions/getInterpretations'
import copyInterpretationState from '../actions/copyInterpretationState'
import prepareStartMode from '../actions/prepareStartMode'
import updateLoadingPhase from '../factories/updateLoadingPhase'
import loadInterpretationData from '../signals/loadInterpretationData'
import selectDefaultInterpretation from '../actions/selectDefaultInterpretation'

export default sequence('loadInterpretations', [
    updateLoadingPhase('start'),
    set(state`views.workflows.loaded`, false),
    updateLoadingPhase('filtering'),
    getInterpretations,
    {
        error: [toast('error', 'Failed to load interpretations', 30000)],
        success: [
            set(state`views.workflows.data.interpretations`, props`result`),
            selectDefaultInterpretation,
            copyInterpretationState,
            prepareStartMode,
            updateLoadingPhase('variants'),
            loadInterpretationData,
            updateLoadingPhase('done')
        ]
    }
])
