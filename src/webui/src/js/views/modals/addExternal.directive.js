/* jshint esnext: true */
import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import template from './addExternal.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('addExternal', {
    templateUrl: 'addExternal.ngtmpl.html',
    controller: connect(
        {
            dismissClicked: signal`views.workflows.modals.addExternal.dismissClicked`,
            selectionChanged: signal`views.workflows.modals.addExternal.selectionChanged`,
            annotationGroups: state`views.workflows.modals.addExternal.annotationGroups`,
            hgncIds: state`views.workflows.modals.addExternal.hgncIds`,
            externalSelected: state`views.workflows.modals.addExternal.selection`,
            saveClicked: signal`views.workflows.modals.addExternal.saveClicked`,
            alleleId: state`views.workflows.modals.addExternal.alleleId`
        },
        'addExternal',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                $ctrl.modelExternalSelected = {}
                Object.assign($ctrl, {
                    getUrls: (group) => {
                        let urls = new Set()
                        if ('url_for_genes' in group) {
                            for (let hgnc_id of $ctrl.hgncIds) {
                                // json data has string keys
                                if (hgnc_id.toString() in group.url_for_genes) {
                                    urls.add(group.url_for_genes[hgnc_id])
                                }
                            }
                        }
                        if ('url' in group) {
                            urls.add(group.url)
                        }
                        return Array.from(urls)
                    }
                })
            }
        ]
    )
})
