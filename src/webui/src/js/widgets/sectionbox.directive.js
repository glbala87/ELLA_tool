/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

/**
 <sectionbox>
 A section box element with vertical header
 */
@Directive({
    selector: 'sectionbox',
    scope: {
        ngDisabled: '=?',
        color: '@'
    },
    transclude: { titlebar: 'titlebar', contentwrapper: 'contentwrapper' },
    template: '<div class="sectionbox" ng-class="vm.color" ng-disabled="vm.ngDisabled"><div class="sb titlebar"><div class="close" ng-if="vm.isModal"></div><div ng-transclude="titlebar"></div></div> <div class="sb-body" ng-transclude="contentwrapper"></div> </div>',
    link: (scope, elem, attrs) => {
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
    }
})
export class SectionboxController { }
