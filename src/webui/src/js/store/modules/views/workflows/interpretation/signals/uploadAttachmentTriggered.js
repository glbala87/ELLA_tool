import { when, push, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'
import postAttachment from '../actions/postAttachment'
import loadAttachments from '../../sequences/loadAttachments'
import checkAttachmentFileSize from '../actions/checkAttachmentFileSize'

export default [
    canUpdateAlleleAssessment,
    {
        true: [
            checkAttachmentFileSize,
            {
                valid: [
                    postAttachment,
                    {
                        success: [
                            setDirty,
                            push(
                                state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.alleleassessment.attachment_ids`,
                                props`result.id`
                            ),
                            loadAttachments
                        ],
                        error: [toast('error', 'Could not upload attachment.')]
                    }
                ],
                invalid: [toast('error', 'Attachment is too big.')]
            }
        ],
        false: [toast('error', 'Could not add attachment.')]
    }
]
