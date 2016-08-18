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
        collapsed: '=?',     // {collapsed: bool}
        collapsible: '=?' // bool: whether card can collapse
    },
    transclude: { cbheader: 'cbheader', cbbody: 'cbbody' },
    template: '<div class="contentbox fixed-width-numbers" ng-class="vm.getClasses()" ng-disabled="vm.ngDisabled"><div class="cb titlebar"><div class="close" ng-click="vm.collapse()" ng-if="vm.isCollapsible()">></div><div ng-transclude="cbheader"></div></div> <div class="cb-body" ng-transclude="cbbody"></div> </div>',
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
            console.log(this.collapsed);
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
