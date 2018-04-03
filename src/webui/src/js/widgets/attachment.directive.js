/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import { AlleleStateHelper } from '../model/allelestatehelper'
import { printedFileSize } from '../util'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import isAlleleAssessmentReused from '../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'

app.component('attachment', {
    bindings: {
        attachmentPath: '<'
    },
    templateUrl: 'ngtmpl/attachment-new.ngtmpl.html',
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

@Directive({
    selector: 'attachment-old',
    scope: {
        attachment: '=',
        onSave: '&?',
        readOnly: '=?',
        allele: '=',
        alleleState: '='
    },
    templateUrl: 'ngtmpl/attachment.ngtmpl.html'
})
export class AttachmentController {
    constructor() {
        this.popover = {
            templateUrl: 'ngtmpl/attachmentPopover.ngtmpl.html'
        }
    }

    getMimeType() {
        let [type, subtype] = this.attachment.mimetype.split('/')
        if (subtype.length > 4) return type.length > 4 ? '?' : type
        else return subtype
    }

    getAlleleAssessment() {
        return AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState)
    }

    removeAttachment() {
        if (this.readOnly) return
        let attachment_ids = AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState)
            .attachment_ids
        let index = attachment_ids.indexOf(this.attachment.id)
        if (index > -1) {
            attachment_ids.splice(index, 1) // Remove attachment
        }
    }

    getVisibility() {
        if (this.readOnly) return 'hidden'
        else return 'visible'
    }

    getPrintedFileSize() {
        return printedFileSize(this.attachment.size)
    }
}
