import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadInterpretationData from './loadInterpretationData'

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
