import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getClassificationDetails from '../actions/getClassificationDetails'
import toast from '../../../../../../common/factories/toast'

export default [
    getClassificationDetails,
    {
        success: [
            set(
                state`views.workflows.modals.alleleAssessmentHistory.classificationDetails`,
                props`result`
            )
        ],
        error: [toast('error', 'Failed to fetch classification details')]
    }
]
