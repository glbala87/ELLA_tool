import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import getFrequencyAnnotation from '../store/common/computes/getFrequencyAnnotation'

app.component('frequencyDetails', {
    bindings: {
        allelePath: '<',
        group: '=' // e.g. name of data set, like ExAC or GNOMAD_EXOMES
    },
    templateUrl: 'ngtmpl/frequencyDetailsWidget.ngtmpl.html',
    controller: connect(
        {
            frequencies: getFrequencyAnnotation(state`${props`allelePath`}`, props`group`)
        },
        'FrequencyDetails',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getFilterFail() {
                        if (!('filter' in $ctrl.frequencies)) {
                            return []
                        }
                        return $ctrl.frequencies.filter.filter((f) => f !== 'PASS')
                    }
                })
            }
        ]
    )
})
