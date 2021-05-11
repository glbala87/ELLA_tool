import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './keyValue.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('keyValue', {
    bindings: {
        source: '@',
        title: '@',
        allelePath: '<',
        configIdx: '@'
    },
    templateUrl: 'keyValue.ngtmpl.html',
    controller: connect(
        {
            data: state`${props`allelePath`}.annotation.${props`source`}`,
            viewConfig: state`app.config.annotation.view.${props`configIdx`}.config`
        },
        'KeyValue',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    wrapData() {
                        return Array.isArray($ctrl.data) ? $ctrl.data : [$ctrl.data]
                    }
                })
            }
        ]
    )
})
