/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {printedFileSize} from '../../util'

@Directive({
    selector: "upload",
    templateUrl: "ngtmpl/upload.ngtmpl.html",
    scope: {
        mode: "=",
        alleleState: "=",
        readOnly: '=?'
    },
})
@Inject('Config', '$element', 'toastr', 'AttachmentResource')
export class UploadController {
    constructor(Config, $element, toastr, AttachmentResource) {
        this.attachmentResource = AttachmentResource;
        this.toastr = toastr;
        this.max_file_size = Config.config.app.max_upload_size;
        $element.bind('change', (e) => {
            this.uploadFiles(e.target.files)
        })
    }

    uploadFiles(files) {
        if (files.length == 0) return;
        for (let file of files) {
            if (file.size > this.max_file_size) {
                this.toastr.error(`Max file size for uploads is ${printedFileSize(this.max_file_size)}`)
                continue;
            }
            this.attachmentResource.post(file).then((attachment_id) => {
                this.alleleState.alleleassessment.attachments.push(attachment_id);
            })
        }
    }
}
