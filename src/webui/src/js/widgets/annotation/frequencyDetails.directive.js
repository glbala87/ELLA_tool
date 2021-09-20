import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './frequencyDetails.ngtmpl.html' // eslint-disable-line no-unused-vars
import getAnnotationConfigItem from '../../store/modules/views/workflows/computed/getAnnotationConfigItem'
import getInterpolatedUrlFromTemplate from '../../store/modules/views/workflows/computed/getInterpolatedUrlFromTemplate'

app.component('frequencyDetails', {
    bindings: {
        source: '@',
        boxTitle: '@',
        url: '@',
        urlEmpty: '@',
        allelePath: '<',
        annotationConfigId: '=',
        annotationConfigItemIdx: '='
    },
    templateUrl: 'frequencyDetails.ngtmpl.html',
    controller: connect(
        {
            frequencies: state`${props`allelePath`}.annotation.${props`source`}`,
            titleUrl: getInterpolatedUrlFromTemplate(props`url`, state`${props`allelePath`}`),
            viewConfig: getAnnotationConfigItem
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
