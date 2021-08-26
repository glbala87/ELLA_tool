import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    ({ state, props }) => {
        const { alleleId } = props
        const annotation = state.get(
            `views.workflows.interpretation.data.alleles.${alleleId}.annotation`
        )
        const annotationGroups = state.get('app.config.custom_annotation.prediction')
        // fetch the annotation from the state and remove keys that are not in the group
        //   to avoid POSTing non-custom annoation
        let annotationPred = annotation.hasOwnProperty('prediction')
            ? deepCopy(annotation.prediction)
            : {}
        const annotationGroupKeys = annotationGroups.map((e) => e.key)
        annotationPred = Object.entries(annotationPred)
            .filter(([k, v]) => annotationGroupKeys.includes(k))
            .reduce((obj, [k, v]) => {
                obj[k] = v
                return obj
            }, {})
        state.set(`views.workflows.modals.addPrediction.selection`, annotationPred)
        state.set(`views.workflows.modals.addPrediction.annotationGroups`, annotationGroups)
    },
    set(state`views.workflows.modals.addPrediction.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addPrediction.show`, true)
]
