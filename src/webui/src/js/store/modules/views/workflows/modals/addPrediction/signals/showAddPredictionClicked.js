import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import { deepCopy } from '../../../../../../../util'

export default [
    ({ state, props }) => {
        const { alleleId } = props
        state.set(
            `views.workflows.modals.addPrediction.selection`,
            deepCopy(
                state.get(
                    `views.workflows.interpretation.data.alleles.${alleleId}.annotation.prediction`
                )
            )
        )
    },
    set(
        state`views.workflows.modals.addPrediction.annotationGroups`,
        state`app.config.custom_annotation.prediction`
    ),
    set(state`views.workflows.modals.addPrediction.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addPrediction.show`, true)
]
