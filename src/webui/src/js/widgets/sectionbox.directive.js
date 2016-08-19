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
        modal: '=?', // bool: whether sectionbox is part of a modal
        color: '@'
    },
    transclude: { titlebar: 'titlebar', contentwrapper: 'contentwrapper' },
    template: '<div class="sectionbox" ng-class="vm.color" ng-disabled="vm.ngDisabled"><div class="sb titlebar"><div class="close" ng-click="vm.close()" ng-if="vm.isModal()">X</div><div ng-transclude="titlebar"></div></div> <div class="sb-body" ng-transclude="contentwrapper"></div> </div>',
    link: (scope, elem, attrs) => { }
})
export class SectionboxController {
    isModal() {
      return (this.modal != undefined || this.modal === true);
    }
    close() {
      this.onClose()();
    }
}
