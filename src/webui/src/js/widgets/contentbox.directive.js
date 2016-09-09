/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

/**
 <contentbox>
 A content box element with vertical header
 */
@Directive({
    selector: 'contentbox',
    scope: {
        color: '@',
        title: '@?', // Title (can also be set through options, options takes precedence)
        titleUrl: '@?',
        collapsed: '=?',
        disabled: '=?',
        collapsible: '=?', // bool: whether box can collapse
    },
    link: (scope, elem, attrs) => {
      setTimeout(() => {
        let e = elem[0].querySelector(".cb-body");
        if(e) {
          let h = e.getBoundingClientRect().width;
          e.style.maxWidth = `${h}px`;
        }
      }, 0);
    },
    transclude: { cbbody: 'cbbody' },
    templateUrl: 'ngtmpl/contentbox.ngtmpl.html'
})
export class ContentboxController {

    constructor() {
        if (this.collapsible === undefined) {
            this.collapsible = true;
        }
    }

    getClasses() {
        let color = this.color ? this.color : "blue";
        let collapsed = this.collapsed ? "collapsed" : "";
        let disabled = this.disabled ? "no-content" : "";
        return `${color} ${collapsed} ${disabled}`;
    }

    collapse() {
        if (this.collapsible) {
            this.collapsed = !Boolean(this.collapsed);
        }
    }
}
