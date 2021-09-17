import { set } from 'cerebral/operators'
import { deepCopy } from '../../../../../../../util'

export default [
    ({ state, props }) => {
        const { source, enable } = props
        let sources = deepCopy(
            state.get(
                'views.workflows.modals.evaluateReference.referenceAssessment.evaluation.sources'
            )
        )
        console.log('Before: ', sources)
        console.log(source, enable)
        if (enable) {
            sources.push(source)
        } else {
            sources = sources.filter((s) => s !== source)
        }
        state.set(
            'views.workflows.modals.evaluateReference.referenceAssessment.evaluation.sources',
            sources
        )
        console.log('After: ', sources)

        // )
        // state.set(
        //     `views.workflows.modals.evaluateReference.referenceAssessment.evaluation.${key}`,
        //     value === undefined || value == '' ? null : value
        // )
    }
]
