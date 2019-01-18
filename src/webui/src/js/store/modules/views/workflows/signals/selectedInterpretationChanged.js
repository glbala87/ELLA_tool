import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadInterpretationData from './loadInterpretationData'
import copyInterpretationState from '../actions/copyInterpretationState'

export default [
    when(props`interpretationId`),
    {
        true: [
            set(state`views.workflows.interpretation.selectedId`, props`interpretationId`),
            copyInterpretationState,
            loadInterpretationData
        ],
        false: []
    }
]
