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
        options: '=?', // {collapsed: bool, url: string, title: string, disabled: bool}
        collapsible: '=?', // bool: whether box can collapse
    },
    link: (scope, elem, attrs) => {
      setTimeout(() => {
        let e = elem[0].querySelector(".cb-body");
        let h = e.getBoundingClientRect().width;
        e.style.maxWidth = `${h}px`;
      }, 0);
    },
    transclude: { cbbody: 'cbbody' },
    templateUrl: 'ngtmpl/contentbox.ngtmpl.html'
})
export class ContentboxController {

    constructor() {
        this.options = this.options || {};
        if (!this.options.title) {
            this.options.title = this.title ? this.title : '';
        }
    }

    getClasses() {
        let color = this.color ? this.color : "blue";
        let collapsed = this.options.collapsed ? "collapsed" : "";
        let disabled = this.isDisabled() ? "no-content" : "";
        return `${color} ${collapsed} ${disabled}`;
    }

    isCollapsible() {
        return this.collapsible === undefined || this.collapsible;
    }

    isDisabled() {
        if (this.options) {
            return this.options.disabled;
        }
        return false;
    }

    collapse() {
        if (this.isCollapsible()) {
            this.options.collapsed === undefined ? true : this.options.collapsed;
            this.options.collapsed = !this.options.collapsed;
        }
    }
}


    // link: (scope, elem, attrs) => {
      // LEAVE FOR NOW!
      //   - fixed padding with alternate CSS rules, but might still need to alter styles here based on children
      //
      // setTimeout(() => {
      //   let e = elem[0].querySelector(".title")
      //   let h = (e.getBoundingClientRect().height * 1.2) + 7;
      //   elem[0].querySelector(".neo-content-box").style.minHeight = h + "px";
      //   if (e.querySelector("a")) {
      //     console.log("TRIGGERED");
      //     elem[0].querySelector(".cb-header").style.backgroundColor = "#4B879B";
      //   }
      // }, 0);
    // }
