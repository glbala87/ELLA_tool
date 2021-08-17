import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    ({ state, props }) => {
        const { alleleId } = props
        const annotation = state.get(
            `views.workflows.interpretation.data.alleles.${alleleId}.annotation`
        )
        const annotationExt = annotation.hasOwnProperty('prediction')
            ? deepCopy(annotation.prediction)
            : {}
        state.set(`views.workflows.modals.addPrediction.selection`, annotationExt)
    },
    set(
        state`views.workflows.modals.addPrediction.annotationGroups`,
        state`app.config.custom_annotation.prediction`
    ),
    set(state`views.workflows.modals.addPrediction.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addPrediction.show`, true)
]
