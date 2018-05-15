import { toggle } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../../interpretation/actions/setDirty'

export default [
    setDirty,
    toggle(
        state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.report.included`
    )
]
