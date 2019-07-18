import { state, props } from 'cerebral/tags'
import { set } from 'cerebral/operators'
import getSortedAlleleAssessments from '../actions/getSortedAlleleAssessments'
import toast from '../../../../../../common/factories/toast'
import updateClassificationDetails from '../sequences/updateClassificationDetails'

export default [
    set(state`views.workflows.modals.alleleAssessmentHistory.show`, true),
    set(state`views.workflows.modals.alleleAssessmentHistory.selectedViewMode`, 'normal'),
    getSortedAlleleAssessments,
    {
        success: [
            set(
                state`views.workflows.modals.alleleAssessmentHistory.data.alleleAssessments`,
                props`result`
            ),
            set(
                state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`,
                state`views.workflows.modals.alleleAssessmentHistory.data.alleleAssessments.0`
            ),
            updateClassificationDetails
        ],
        error: [toast('error', 'Failed to load classifications')]
    }
]
