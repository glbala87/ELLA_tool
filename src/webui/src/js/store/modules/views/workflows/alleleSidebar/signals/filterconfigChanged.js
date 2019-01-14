import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadInterpretationData from '../../signals/loadInterpretationData'

export default [
    set(state`views.workflows.interpretation.selected.state.filterconfigId`, props`filterconfigId`),
    loadInterpretationData
]
