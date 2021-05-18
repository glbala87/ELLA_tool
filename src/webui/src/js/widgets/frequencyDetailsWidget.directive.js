import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './frequencyDetailsWidget.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('frequencyDetails', {
    bindings: {
        source: '@',
        title: '@',
        allelePath: '<',
        configIdx: '@'
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
                    },
                    shouldShowIndications(key) {
                        if (
                            'indications' in $ctrl.viewConfig &&
                            $ctrl.viewConfig.indications.keys.includes(key)
                        ) {
                            let threshold = $ctrl.viewConfig.indications.threshold || Infinity
                            if (threshold === Infinity) {
                                return true
                            } else {
                                return (
                                    'count' in $ctrl.frequencies &&
                                    key in $ctrl.frequencies.count &&
                                    $ctrl.frequencies.count[key] < threshold
                                )
                            }
                        }
                    }
                })
            }
        ]
    )
})
