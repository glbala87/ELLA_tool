import { set, when, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import startWorkflow from '../factories/startWorkflow'
import loadInterpretations from '../sequences/loadInterpretations'
import toast from '../../../../common/factories/toast'

// After starting the workflow, we need to reload
// all the data from backend (via loadInterpretations) to get
// correct data make sure everything is setup correctly.

export default [
    startWorkflow('override'),
    {
        success: [loadInterpretations],
        error: [toast('error', 'Something went wrong when reassigning workflow.')]
    }
]
