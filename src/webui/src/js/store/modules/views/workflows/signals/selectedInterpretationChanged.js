import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareInterpretationState from '../actions/prepareInterpretationState'
import loadInterpretationData from './loadInterpretationData'

export default [
    when(props`interpretation`),
    {
        true: [
            set(state`views.workflows.interpretation.selected`, props`interpretation`),
            // Historical interpretations might not have all required state fields
            // These changes will not be persisted to backend
            prepareInterpretationState,
            loadInterpretationData
        ],
        false: []
    }
]
