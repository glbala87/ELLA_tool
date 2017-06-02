/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

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
        let attachments = AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState).attachments;
        let index = attachments.indexOf(this.attachment.id);
        if (index > -1) {
            attachments.splice(index, 1); // Remove attachment
        }
    }

    getVisibility() {
        if (this.readOnly) return "hidden";
        else return "visible";
    }

    getPrintedFileSize() {
        let size = this.attachment.size;
        var i = Math.floor( Math.log(size) / Math.log(1024) );
        if (i > 2) i = 2;
        return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB'][i];
    }
}
