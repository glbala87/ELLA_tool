import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import saveInterpretation from '../sequences/saveInterpretation'
import startWorkflow from '../factories/startWorkflow'
import loadInterpretations from '../sequences/loadInterpretations'
import toastr from '../../../../common/factories/toastr'

// After starting the workflow, we need to reload
// all the data from backend (via loadInterpretations) to get
// correct data make sure everything is setup correctly.

export default [
    equals(state`views.workflows.startMode`),
    {
        save: [saveInterpretation([])],
        override: [
            startWorkflow('override'),
            {
                success: [loadInterpretations],
                error: [toastr('error', 'Something went wrong when reassigning workflow.')]
            }
        ],
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
        start: [
            startWorkflow('start'),
            {
                success: [loadInterpretations],
                error: [toastr('error', 'Something went wrong when starting workflow.')]
            }
        ],
        review: [
            // same as start on backend
            startWorkflow('start'),
            {
                success: [loadInterpretations],
                error: [toastr('error', 'Something went wrong when starting workflow for review.')]
            }
        ]
    }
]
