import { sequence } from 'cerebral'
import { set, when } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getInterpretations from '../actions/getInterpretations'
import copyInterpretationState from '../actions/copyInterpretationState'
import prepareStartMode from '../actions/prepareStartMode'
import updateLoadingPhase from '../factories/updateLoadingPhase'
import loadInterpretationData from '../signals/loadInterpretationData'
import selectDefaultInterpretation from '../actions/selectDefaultInterpretation'
import getFilterConfigs from '../actions/getFilterConfigs'
import setDefaultFilterConfig from '../actions/setDefaultFilterConfig'

export default sequence('loadInterpretations', [
    updateLoadingPhase('start'),
    set(state`views.workflows.loaded`, false),
    getFilterConfigs,
    {
        error: [toast('error', 'Failed to load filter configs', 30000)],
        success: [
            set(state`views.workflows.data.filterconfigs`, props`result`),
            getInterpretations,
            {
                error: [toast('error', 'Failed to load interpretations', 30000)],
                success: [
                    set(state`views.workflows.data.interpretations`, props`result`),
                    selectDefaultInterpretation,
                    copyInterpretationState,
                    when(state`views.workflows.type`, (type) => type === 'analysis'),
                    {
                        true: [setDefaultFilterConfig],
                        false: []
                    },
                    prepareStartMode,
                    updateLoadingPhase('variants'),
                    loadInterpretationData,
                    updateLoadingPhase('done')
                ]
            }
        ]
    }
])
