import { set, when, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import saveInterpretation from '../sequences/saveInterpretation'
import startWorkflow from '../factories/startWorkflow'
import loadInterpretations from '../sequences/loadInterpretations'
import toastr from '../../../../common/factories/toastr'
import showModal from '../../../../common/actions/showModal'

// After starting the workflow, we need to reload
// all the data from backend (via loadInterpretations) to get
// correct data make sure everything is setup correctly.

const startWorkflowSequence = [
    startWorkflow('start'),
    {
        success: [loadInterpretations],
        error: [toastr('error', 'Something went wrong when starting workflow.')]
    }
]

export default [
    equals(state`views.workflows.startMode`),
    {
        save: [saveInterpretation([])],
        override: [set(props`modalName`, string`reassignWorkflow`), showModal],
        reopen: [
            startWorkflow('reopen'),
            {
                success: [
                    when(props`startWhenReopen`),
                    {
                        true: [
                            startWorkflow('start'),
                            {
                                success: [loadInterpretations],
                                error: [
                                    toastr('error', 'Something went wrong when starting workflow.')
                                ]
                            }
                        ],
                        false: [loadInterpretations]
                    }
                ],
                error: [toastr('error', 'Something went wrong when reopening workflow.')]
            }
        ],
        'Not ready': startWorkflowSequence,
        Interpretation: startWorkflowSequence,
        Review: startWorkflowSequence,
        'Medical review': startWorkflowSequence
    }
]
