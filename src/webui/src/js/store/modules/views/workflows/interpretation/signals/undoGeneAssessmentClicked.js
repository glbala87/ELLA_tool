import { unset } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    unset(state`views.workflows.interpretation.geneInformation.geneassessment.${props`hgncId`}`)
]
