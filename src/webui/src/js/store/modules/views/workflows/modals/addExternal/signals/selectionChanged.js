import { set } from 'cerebral/operators'

export default [
    ({ state, props }) => {
        const { key, value } = props
        state.set(
            `views.workflows.modals.addExternal.selection.${key}`,
            value === undefined || value == '' ? null : value
        )
    }
]
