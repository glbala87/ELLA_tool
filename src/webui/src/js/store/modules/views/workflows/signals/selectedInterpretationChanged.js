import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadInterpretationData from './loadInterpretationData'
import prepareSelectedInterpretation from '../actions/prepareSelectedInterpretation'

export default [
    when(props`interpretationId`),
    {
        true: [
            set(state`views.workflows.interpretation.selectedId`, props`interpretationId`),
            prepareSelectedInterpretation,
            loadInterpretationData
        ],
        false: []
    }
]
