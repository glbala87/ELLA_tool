/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './showAnalysesForAllele.ngtmpl.html'

app.component('showAnalysesForAllele', {
    template,
    controller: connect(
        {
            analyses: state`modals.showAnalysesForAllele.data.analyses`,
            allele: state`modals.showAnalysesForAllele.allele`,
            showAnalysesForAlleleAccepted: signal`modals.showAnalysesForAlleleAccepted`,
            copyAnalysesForAlleleClicked: signal`modals.copyAnalysesForAlleleClicked`,
            closeClicked: signal`closeModal`
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
                    isAccepted() {
                        return $ctrl.accepted || false
                    },
                    accept() {
                        $ctrl.accepted = true
                        $ctrl.showAnalysesForAlleleAccepted({ alleleId: $ctrl.allele.id })
                    },
                    close() {
                        $ctrl.closeClicked({ modalName: 'showAnalysesForAllele' })
                    }
                })
            }
        ]
    )
})
