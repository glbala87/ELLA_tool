import { unset } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDirty from '../actions/setDirty'
import isReadOnly from '../operators/isReadOnly'

export default [
    isReadOnly,
    {
        true: [],
        false: [
            unset(state`views.workflows.interpretation.userState.geneassessment.${props`hgncId`}`),
            setDirty
        ]
    }
]
