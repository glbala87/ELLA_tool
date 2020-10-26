import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'
import getAlleleAssessments from '../actions/getAlleleAssessments'
import getAttachmentsById from '../actions/getAttachmentsById'

export default [
    set(state`views.workflows.modals.alleleAssessmentHistory.show`, true),
    getAlleleAssessments,
    {
        success: [
            set(
                state`views.workflows.modals.alleleAssessmentHistory.data.alleleassessments`,
                props`result`
            ),
            set(
                state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`,
                state`views.workflows.modals.alleleAssessmentHistory.data.alleleassessments.0`
            ),
            ({ state }) => {
                const alleleassessments = state.get(
                    'views.workflows.modals.alleleAssessmentHistory.data.alleleassessments'
                )
                const attachmentIds = alleleassessments
                    .map((aa) => aa.attachment_ids)
                    .reduce((a, b) => a.concat(b))

                return { attachmentIds: Array.from(new Set(attachmentIds)) }
            },
            getAttachmentsById,
            {
                success: [
                    set(
                        state`views.workflows.modals.alleleAssessmentHistory.data.attachments`,
                        props`result`
                    )
                ],
                error: [toast('error', 'Failed to load attachments')]
            }
        ],
        error: [toast('error', 'Failed to load alleleassessments')]
    }
]
