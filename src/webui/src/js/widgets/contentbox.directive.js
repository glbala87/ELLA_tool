/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import template from './contentbox.ngtmpl.html'

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
}
