import { set } from 'cerebral/operators'

export default [
    ({ state, props }) => {
        const { key, value } = props
        state.set(
            `views.workflows.modals.addPrediction.selection.${key}`,
            value === undefined ? null : value
        )
    }
]
