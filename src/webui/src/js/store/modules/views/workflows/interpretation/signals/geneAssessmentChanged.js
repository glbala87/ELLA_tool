import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(
        state`views.workflows.interpretation.geneInformation.geneassessment.${props`hgncId`}`,
        props`geneAssessment`
    )
]
