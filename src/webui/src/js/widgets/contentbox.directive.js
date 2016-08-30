/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

/**
 <contentbox>
 A content box element with vertical header
 */
@Directive({
    selector: 'contentbox',
    scope: {
        ngDisabled: '=?',
        color: '@',
        collapsed: '=?',
        collapsible: '=?' // bool: whether card can collapse
    },
    transclude: { cbheader: 'cbheader', cbbody: 'cbbody' },
    link: (scope, elem, attrs) => {
      setTimeout(() => {
        let e = elem[0].querySelector(".cb-body");
        let h = e.getBoundingClientRect().width;
        e.style.maxWidth = `${h}px`;
      }, 0);
    },
    template: ' \
        <div class="contentbox fixed-width-numbers" ng-class="vm.getClasses()" ng-disabled="vm.ngDisabled"> \
          <div class="cb titlebar"> \
            <div ng-transclude="cbheader"></div> \
            <div class="close" ng-click="vm.collapse()" ng-class="{collapsed: vm.collapsed}" ng-if="vm.isCollapsible()"> \
              <svg id="i-play" viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="currentcolor" stroke-linecap="round" stroke-linejoin="round" stroke-width="6.25%"> \
                  <path d="M10 2 L10 30 24 16 Z" /> \
              </svg> \
            </div> \
          </div> \
          <div class="cb-body" ng-transclude="cbbody"></div> \
        </div>',
})
export class ContentboxController {
    getClasses() {
      let color = this.color ? this.color : "blue";
      let collapsed = this.collapsed ? "collapsed" : "";
      return `${color} ${collapsed}`
    }
    isCollapsible() {
      return this.collapsible === undefined || this.collapsible;
    }
    collapse() {
        if (this.isCollapsible()) {
            this.collapsed === undefined ? true : this.collapsed;
            this.collapsed = !this.collapsed;
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
