import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import template from './upload.ngtmpl.html'

app.component('upload', {
    bindings: {
        mode: '<',
        buttontext: '<'
    },
    templateUrl: 'upload.ngtmpl.html',
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
                            $ctrl.uploadAttachment({ alleleId: $ctrl.selectedAllele, file })
                        }
                    }
                })

                function setupBrowseMode() {
                    $element.bind('change', (e) => {
                        $ctrl.uploadFiles(e.target.files)
                        e.target.value = ''
                    })
                }

                function setupDropMode() {
                    $element.bind('drop', (e) => {
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
