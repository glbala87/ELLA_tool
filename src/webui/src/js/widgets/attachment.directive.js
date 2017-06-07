/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';
import {printedFileSize} from '../util'

@Directive({
    selector: 'attachment',
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
        let [type, subtype] = this.attachment.mimetype.split("/");
        if (subtype.length > 4) return type.length > 4 ? "?" : type;
        else return subtype;
    }

    getAlleleAssessment() {
        return AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState)
    }

    removeAttachment() {
        if (this.readOnly) return;
        let attachment_ids = AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState).attachment_ids;
        let index = attachment_ids.indexOf(this.attachment.id);
        if (index > -1) {
            attachment_ids.splice(index, 1); // Remove attachment
        }
    }

    getVisibility() {
        if (this.readOnly) return "hidden";
        else return "visible";
    }

    getPrintedFileSize() {
        return printedFileSize(this.attachment.size)
    }
}
