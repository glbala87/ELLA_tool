/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import { printedFileSize } from '../../util'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

app.component('upload', {
    bindings: {
        mode: '<',
        buttontext: '<'
    },
    templateUrl: 'ngtmpl/upload-new.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            readOnly: isReadOnly,
            selectedAllele: state`views.workflows.selectedAllele`,
            uploadAttachment: signal`views.workflows.interpretation.uploadAttachmentTriggered`
        },
        'Upload',
        [
            '$scope',
            '$element',
            function($scope, $element) {
                const $ctrl = $scope.$ctrl

                Object.assign($scope.$ctrl, {
                    isUploadEnabled() {
                        return Boolean($ctrl.config.app.attachment_storage)
                    },
                    getOpacity() {
                        return $ctrl.dragCount > 0 ? 0.75 : 0.25
                    },
                    uploadFiles(files) {
                        if (files.length == 0) return
                        for (let file of files) {
                            /* if (file.size > $ctrl.config.app.max_upload_size) {
                                this.toastr.error(
                                    `File '${file.name}' is too big (${printedFileSize(
                                        file.size
                                    )}). Max size is ${printedFileSize(this.max_file_size)}.`
                                )
                                continue
                            } */
                            $ctrl.uploadAttachment({ alleleId: $ctrl.selectedAllele, file })
                        }
                    }
                })

                function setupBrowseMode() {
                    $element.bind('change', e => {
                        $ctrl.uploadFiles(e.target.files)
                        e.target.value = ''
                    })
                }

                function setupDropMode() {
                    $element.bind('drop', e => {
                        $ctrl.dragCount = 0
                        e.preventDefault()
                        $ctrl.uploadFiles(e.dataTransfer.files)
                    })

                    $element.bind('dragenter', () => {
                        $ctrl.dragCount++
                        $scope.$digest()
                    })

                    $element.bind('dragleave', () => {
                        $ctrl.dragCount--
                        $scope.$digest()
                    })
                }

                if ($ctrl.mode === 'browse') {
                    setupBrowseMode()
                } else if ($ctrl.mode === 'drop') {
                    $ctrl.dragCount = 0
                    setupDropMode()
                }
            }
        ]
    )
})

@Directive({
    selector: 'upload-old',
    templateUrl: 'ngtmpl/upload.ngtmpl.html',
    scope: {
        mode: '=',
        buttontext: '=',
        alleleState: '=',
        readOnly: '=?'
    }
})
@Inject('$scope', 'Config', '$element', 'toastr', 'AttachmentResource')
export class UploadController {
    constructor($scope, Config, $element, toastr, AttachmentResource) {
        this.scope = $scope
        this.attachmentResource = AttachmentResource
        this.toastr = toastr
        this.max_file_size = Config.config.app.max_upload_size
        this.uploadEnabled = Boolean(Config.config.app.attachment_storage)
        this.element = $element
        if (this.mode === 'browse') {
            this.setupBrowseMode()
        } else if (this.mode === 'drop') {
            this.dragCount = 0
            this.setupDropMode()
        }
    }

    setupBrowseMode() {
        this.element.bind('change', e => {
            this.uploadFiles(e.target.files)
            e.target.value = ''
        })
    }

    setupDropMode() {
        this.element.bind('drop', e => {
            this.dragCount = 0
            e.preventDefault()
            this.uploadFiles(e.dataTransfer.files)
        })

        this.element.bind('dragenter', () => {
            this.dragCount++
            this.scope.$digest()
        })

        this.element.bind('dragleave', () => {
            this.dragCount--
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
        if (files.length == 0) return
        for (let file of files) {
            this.attachmentResource.post(file).then(attachment_id => {
                this.alleleState.alleleassessment.attachment_ids.push(attachment_id)
            })
        }
    }
}
