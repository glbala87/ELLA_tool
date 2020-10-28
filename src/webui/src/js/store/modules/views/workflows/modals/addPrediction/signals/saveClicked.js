import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postCustomAnnotation from '../../../../workflows/interpretation/sequences/postCustomAnnotation'

export default [
    postCustomAnnotation,
    set(state`views.workflows.modals.addPrediction`, { show: false })
]
