import { sequence } from 'cerebral'
import { set, when } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getInterpretations from '../actions/getInterpretations'
import copyInterpretationState from '../actions/copyInterpretationState'
import prepareStartMode from '../actions/prepareStartMode'
import loadInterpretationData from '../signals/loadInterpretationData'
import selectDefaultInterpretation from '../actions/selectDefaultInterpretation'
import getFilterConfigs from '../actions/getFilterConfigs'

export default sequence('loadInterpretations', [
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

                    prepareStartMode,
                    loadInterpretationData
                ]
            }
        ]
    }
])
