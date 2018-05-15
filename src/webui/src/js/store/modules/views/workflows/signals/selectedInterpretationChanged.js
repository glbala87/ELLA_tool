import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareInterpretationState from '../actions/prepareInterpretationState'
import loadInterpretationData from './loadInterpretationData'
import prepareSelectedInterpretation from '../actions/prepareSelectedInterpretation'

export default [
    when(props`interpretation`),
    {
        true: [
            set(state`views.workflows.interpretation.selected`, props`interpretation`),
            loadInterpretationData
        ],
        false: []
    }
]
