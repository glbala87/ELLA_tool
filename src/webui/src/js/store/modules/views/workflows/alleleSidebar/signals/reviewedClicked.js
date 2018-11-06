import { toggle, set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../../interpretation/actions/setDirty'
import isReadOnly from '../../interpretation/operators/isReadOnly'

export default [
    isReadOnly,
    {
        true: [],
        false: [
            when(
                state`views.workflows.interpretation.selected.state.allele`,
                props`alleleId`,
                (alleleState, alleleId) => alleleId in alleleState
            ),
            {
                true: [
                    toggle(
                        state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.workflow.reviewed`
                    ),
                    setDirty
                ],
                false: []
            }
        ]
    }
]
