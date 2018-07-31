import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './alleleInfoQuality.ngtmpl.html'

app.component('alleleInfoQuality', {
    template,
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
