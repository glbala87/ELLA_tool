import { set, equals } from 'cerebral/operators'
import { props, string } from 'cerebral/tags'
import { goTo } from '@cerebral/router/operators'
import saveInterpretation from '../sequences/saveInterpretation'
import finishWorkflow from '../factories/finishWorkflow'
import toast from '../../../../common/factories/toast'
import closeModal from '../../../../common/actions/closeModal'
import finishAllowed from '../factories/finishAllowed'

const finishWorkflowWithStatus = (status) => {
    return [
        finishAllowed(status),
        {
            true: [
                saveInterpretation([
                    finishWorkflow(status),
                    {
                        success: [goTo('/overview')],
                        error: [
                            toast('error', `Something went wrong while marking workflow ${status}`)
                        ]
                    }
                ])
            ],
            false: [toast('error', string`${props`errorMessage`}`)]
        }
    ]
}

export default [
    equals(props`workflowStatus`),
    {
        'Not ready': finishWorkflowWithStatus('Not ready'),
        Interpretation: finishWorkflowWithStatus('Interpretation'),
        Review: finishWorkflowWithStatus('Review'),
        'Medical review': finishWorkflowWithStatus('Medical review'),
        Finalized: finishWorkflowWithStatus('Finalized')
    },
    set(props`modalName`, 'finishConfirmation'),
    closeModal
]
