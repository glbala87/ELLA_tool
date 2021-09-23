/* jshint esnext: true */
import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'

import template from './contentbox.ngtmpl.html' // eslint-disable-line no-unused-vars

/**
 <contentbox>
 A content box element with vertical header
 */
app.component('contentbox', {
    bindings: {
        color: '@',
        boxtitle: '@?',
        titleUrl: '@?',
        disabledTitleUrl: '@?',
        disabled: '=?'
    },
    transclude: { cbbody: 'cbbody' },
    templateUrl: 'contentbox.ngtmpl.html',
    controller: connect(
        {},
        'sectionbox',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getClasses() {
                        let color = this.color ? this.color : 'blue'
                        let disabled = this.disabled ? 'no-content' : ''
                        return `${color} ${disabled}`
                    },
                    getUrl() {
                        return this.disabled ? this.disabledTitleUrl : this.titleUrl
                    }
                })
            }
        ]
    )
})
