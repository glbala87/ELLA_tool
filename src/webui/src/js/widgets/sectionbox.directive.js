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
    transclude: { titlebar: 'titlebar', contentwrapper: 'contentwrapper', controls: '?controls' },
    template: '<section class="sectionbox" ng-class="vm.color" ng-disabled="vm.ngDisabled"> \
      <header class="sb titlebar"> \
        <div class="close" ng-click="vm.close()" ng-if="vm.isModal()">X</div> \
        <div ng-transclude="titlebar"></div> \
      </header> \
      <article class="sb-body" ng-transclude="contentwrapper"></article> \
      <aside class="sb-controls" ng-transclude="controls"></aside> \
    </section>',
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
