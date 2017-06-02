/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: "upload",
    templateUrl: "ngtmpl/upload.ngtmpl.html",
    scope: {
        mode: "=",
        alleleState: "=",
        readOnly: '=?'
    },
})
@Inject('$element', 'AttachmentResource')
export class UploadController {
    constructor($element, AttachmentResource) {
        this.attachmentResource = AttachmentResource;
        $element.bind('change', (e) => {
            this.uploadFiles(e.target.files)
        })
    }

    uploadFiles(files) {
        if (files.length == 0) return;
        for (let file of files) {
            this.attachmentResource.post(file).then((attachment_id) => {
                this.alleleState.alleleassessment.attachments.push(attachment_id);
            })
        }
    }
}
