import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import getFrequencyAnnotation from '../store/common/computes/getFrequencyAnnotation'
import template from './frequencyDetailsWidgetLegacy.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('frequencyDetailsLegacy', {
    bindings: {
        allelePath: '<',
        group: '=' // e.g. name of data set, like ExAC or GNOMAD_EXOMES
    },
    templateUrl: 'frequencyDetailsWidgetLegacy.ngtmpl.html',
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
                        if (!($ctrl.frequencies && 'filter' in $ctrl.frequencies)) {
                            return []
                        }
                        return $ctrl.frequencies.filter.filter((f) => f !== 'PASS')
                    }
                })
            }
        ]
    )
})
