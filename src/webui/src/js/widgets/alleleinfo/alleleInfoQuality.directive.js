import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleInfoQuality', {
    templateUrl: 'ngtmpl/alleleInfoQuality.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoQuality',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    formatSequence: (sequence) => {
                        if (sequence.length > 10) {
                            return `(${sequence.length})`
                        } else {
                            return sequence
                        }
                    }
                })
            }
        ]
    )
})
