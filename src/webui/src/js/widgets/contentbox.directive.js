/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import template from './contentbox.ngtmpl.html' // eslint-disable-line no-unused-vars

/**
 <contentbox>
 A content box element with vertical header
 */
@Directive({
    selector: 'contentbox',
    scope: {
        color: '@',
        boxtitle: '@?',
        titleUrl: '@?',
        disabledTitleUrl: '@?',
        disabled: '=?'
    },
    transclude: { cbbody: 'cbbody' },
    template
})
@Inject('$scope')
export class ContentboxController {
    constructor() {}

    getClasses() {
        let color = this.color ? this.color : 'blue'
        let disabled = this.disabled ? 'no-content' : ''
        return `${color} ${disabled}`
    }
    getUrl() {
        return this.disabled ? this.disabledTitleUrl : this.titleUrl
    }
}
