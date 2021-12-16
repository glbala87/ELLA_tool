import { debounce } from 'cerebral/operators'

export default [
    debounce(200),
    {
        continue: [
            ({ state, props }) => {
                const { key, value } = props
                state.set(
                    `views.workflows.modals.evaluateReference.referenceAssessment.evaluation.${key}`,
                    value === undefined ? null : value
                )
            }
        ],
        discard: []
    }
]
