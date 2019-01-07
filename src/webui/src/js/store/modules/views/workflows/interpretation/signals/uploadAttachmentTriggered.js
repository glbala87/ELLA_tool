import { push } from 'cerebral/operators';
import { props, state } from 'cerebral/tags';
import toast from '../../../../../common/factories/toast';
import loadAttachments from '../../sequences/loadAttachments';
import checkAttachmentFileSize from '../actions/checkAttachmentFileSize';
import postAttachment from '../actions/postAttachment';
import setDirty from '../actions/setDirty';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';

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
