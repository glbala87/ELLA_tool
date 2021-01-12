/* jshint esnext: true */
import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import template from './addPrediction.ngtmpl.html'

app.component('addPrediction', {
    templateUrl: 'addPrediction.ngtmpl.html',
    controller: connect(
        {
            dismissClicked: signal`views.workflows.modals.addPrediction.dismissClicked`,
            selectionChanged: signal`views.workflows.modals.addPrediction.selectionChanged`,
            annotationGroups: state`views.workflows.modals.addPrediction.annotationGroups`,
            predictionSelected: state`views.workflows.modals.addPrediction.selection`,
            saveClicked: signal`views.workflows.modals.addPrediction.saveClicked`,
            alleleId: state`views.workflows.modals.addPrediction.alleleId`
        },
        'AddPrediction',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                $ctrl.modelPredictionSelected = {}
            }
        ]
    )
})
