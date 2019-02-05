/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './showAnalysesForAllele.ngtmpl.html'

app.component('showAnalysesForAllele', {
    templateUrl: 'showAnalysesForAllele.ngtmpl.html',
    controller: connect(
        {
            analyses: state`search.modals.showAnalysesForAllele.data.analyses`,
            allele: state`search.modals.showAnalysesForAllele.allele`,
            warningAccepted: state`search.modals.showAnalysesForAllele.warningAccepted`,
            warningAcceptedClicked: signal`search.modals.showAnalysesForAllele.warningAcceptedClicked`,
            copyAnalysesForAlleleClicked: signal`search.modals.showAnalysesForAllele.copyAnalysesForAlleleClicked`,
            dismissClicked: signal`search.modals.showAnalysesForAllele.dismissClicked`
        },
        'ShowAnalysesForAllele',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getColor() {
                        return $ctrl.accepted ? 'blue' : 'red'
                    },
                    accept() {
                        $ctrl.warningAcceptedClicked({ alleleId: $ctrl.allele.id })
                    },
                    close() {
                        $ctrl.dismissClicked()
                    }
                })
            }
        ]
    )
})
