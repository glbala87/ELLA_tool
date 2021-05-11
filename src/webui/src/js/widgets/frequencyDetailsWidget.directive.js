import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import getFrequencyAnnotation from '../store/common/computes/getFrequencyAnnotation'
import template from './frequencyDetailsWidget.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('frequencyDetails', {
    bindings: {
        source: '@',
        title: '@',
        allelePath: '<',
        configIdx: '@',
        columns: '=', // e.g. name of data set, like ExAC or GNOMAD_EXOMES
        rows: '='
    },
    templateUrl: 'frequencyDetailsWidget.ngtmpl.html',
    controller: connect(
        {
            frequencies: state`${props`allelePath`}.annotation.${props`source`}`,
            viewConfig: state`app.config.annotation.view.${props`configIdx`}.config`
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
                        const filterValues = [].concat.apply(
                            [],
                            Object.values($ctrl.frequencies.filter)
                        )
                        return filterValues.filter((f) => f !== 'PASS')
                    }
                })
            }
        ]
    )
})
