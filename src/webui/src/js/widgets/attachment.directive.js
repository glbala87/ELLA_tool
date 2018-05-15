import app from '../ng-decorators'
import { printedFileSize } from '../util'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import isAlleleAssessmentReused from '../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'

app.component('attachment', {
    bindings: {
        attachmentPath: '<'
    },
    templateUrl: 'ngtmpl/attachment.ngtmpl.html',
    controller: connect(
        {
            readOnly: isReadOnly,
            reused: isAlleleAssessmentReused(state`views.workflows.selectedAllele`),
            selectedAllele: state`views.workflows.selectedAllele`,
            attachment: state`${props`attachmentPath`}`,
            removeAttachment: signal`views.workflows.interpretation.removeAttachmentClicked`
        },
        'Attachment',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($scope.$ctrl, {
                    getMimeType() {
                        let [type, subtype] = $ctrl.attachment.mimetype.split('/')
                        if (subtype.length > 4) {
                            return type.length > 4 ? '?' : type
                        } else {
                            return subtype
                        }
                    },
                    getPopoverTemplate() {
                        return 'ngtmpl/attachmentPopover.ngtmpl.html'
                    },
                    getPrintedFileSize() {
                        return printedFileSize($ctrl.attachment.size)
                    },
                    getVisibility() {
                        return $ctrl.readOnly ? 'hidden' : 'visible'
                    }
                })
            }
        ]
    )
})
