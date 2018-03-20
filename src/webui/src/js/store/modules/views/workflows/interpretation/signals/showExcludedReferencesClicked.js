import { toggle } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    toggle(
        state`views.workflows.interpretation.selected.user_state.allele.${props`alleleId`}.showExcludedReferences`
    )
]
