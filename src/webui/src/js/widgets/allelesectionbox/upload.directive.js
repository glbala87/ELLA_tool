/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {printedFileSize} from '../../util'

@Directive({
    selector: "upload",
    templateUrl: "ngtmpl/upload.ngtmpl.html",
    scope: {
        mode: "=",
        buttontext: "=",
        alleleState: "=",
        readOnly: '=?'
    },
})
@Inject('$scope', 'Config', '$element', 'toastr', 'AttachmentResource')
export class UploadController {
    constructor($scope, Config, $element, toastr, AttachmentResource) {
        this.scope = $scope;
        this.attachmentResource = AttachmentResource;
        this.toastr = toastr;
        this.max_file_size = Config.config.app.max_upload_size;
        this.element = $element;
        if (this.mode === "browse") {
            this.setupBrowseMode()
        } else if (this.mode === "drop") {
            this.dragCount = 0;
            this.setupDropMode()
        }


    }

    setupBrowseMode() {
        this.element.bind('change', (e) => {
            this.uploadFiles(e.target.files)
            e.target.value = "";
        })
    }

    setupDropMode() {
        this.element.bind('drop', (e) => {
            this.dragCount = 0;
            e.preventDefault()
            this.uploadFiles(e.dataTransfer.files)
        })

        this.element.bind('dragenter', () => {
            this.dragCount++;
            this.scope.$digest()
        })

        this.element.bind('dragleave', () => {
            this.dragCount--;
            this.scope.$digest()
        })
    }

    getOpacity() {
        if (this.dragCount > 0) {
            return 0.75
        } else {
            return 0.25
        }
    }

    uploadFiles(files) {
        if (files.length == 0) return;
        for (let file of files) {
            if (file.size > this.max_file_size) {
                this.toastr.error(`Max file size for uploads is ${printedFileSize(this.max_file_size)}`)
                continue;
            }
            this.attachmentResource.post(file).then((attachment_id) => {
                this.alleleState.alleleassessment.attachment_ids.push(attachment_id);
            })
        }
    }
}
