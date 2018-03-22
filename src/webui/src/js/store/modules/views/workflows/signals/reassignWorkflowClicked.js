import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import startWorkflow from '../factories/startWorkflow'
import loadInterpretations from '../sequences/loadInterpretations'
import toastr from '../../../../common/factories/toastr'

// After starting the workflow, we need to reload
// all the data from backend (via loadInterpretations) to get
// correct data make sure everything is setup correctly.

export default [
    startWorkflow('override'),
    {
        success: [loadInterpretations],
        error: [toastr('error', 'Something went wrong when reassigning workflow.')]
    }
]
