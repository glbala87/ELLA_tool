import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'
import getAlleleAssessments from '../actions/getAlleleAssessments'
import getAlleleReports from '../actions/getAlleleReports'
import getAttachmentsById from '../actions/getAttachmentsById'

export default [
    set(state`views.workflows.modals.alleleHistory.show`, true),
    set(state`views.workflows.modals.alleleHistory.selectedMode`, 'classification'),
    getAlleleAssessments,
    {
        success: [
            set(state`views.workflows.modals.alleleHistory.data.alleleassessments`, props`result`),
            set(
                state`views.workflows.modals.alleleHistory.selected`,
                state`views.workflows.modals.alleleHistory.data.alleleassessments.0`
            ),
            ({ state }) => {
                const alleleassessments = state.get(
                    'views.workflows.modals.alleleHistory.data.alleleassessments'
                )
                const attachmentIds = alleleassessments
                    .map((aa) => aa.attachment_ids)
                    .reduce((a, b) => a.concat(b))

                return { attachmentIds: Array.from(new Set(attachmentIds)) }
            },
            getAttachmentsById,
            {
                success: [
                    set(state`views.workflows.modals.alleleHistory.data.attachments`, props`result`)
                ],
                error: [toast('error', 'Failed to load attachments')]
            }
        ],
        error: [toast('error', 'Failed to load alleleassessments')]
    },
    getAlleleReports,
    {
        success: [
            set(state`views.workflows.modals.alleleHistory.data.allelereports`, props`result`)
        ],
        error: [toast('error', 'Failed to load allele reports')]
    }
]
