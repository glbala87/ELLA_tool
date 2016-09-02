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
        topcontrols: '=?', // bool: whether controls should live at the top of the section
        collapsed: '=?',
        color: '@'
    },
    transclude: { titlebar: 'titlebar', contentwrapper: 'contentwrapper', controls: '?controls' },
    template: '<section class="sectionbox" ng-class="vm.getClasses()" ng-disabled="vm.ngDisabled"> \
      <header class="sb titlebar"> \
        <div class="icon modal-close" ng-click="vm.close()" ng-if="vm.isModal()"> \
          <svg id="i-close" viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="currentcolor" stroke-linecap="round" stroke-linejoin="round" stroke-width="6.25%"> \
            <path d="M2 30 L30 2 M30 30 L2 2" /> \
          </svg> \
        </div> \
        <div ng-transclude="titlebar"></div> \
        <div class="icon collapser" ng-if="!vm.isModal()" ng-click="vm.collapse()"> \
          <svg id="i-play" viewBox="0 0 32 32" width="32" height="32" fill="currentcolor" stroke="currentcolor" stroke-linecap="round" stroke-linejoin="round" stroke-width="6.25%"> \
              <path d="M10 2 L10 30 24 16 Z" /> \
          </svg> \
        </div> \
      </header> \
      <div class="sb-container" ng-class="{topcontrols: vm.onTop()}"> \
        <aside class="sb-controls" ng-transclude="controls"></aside> \
        <article class="sb-body" ng-transclude="contentwrapper"></article> \
      </div> \
    </section>',
    link: (scope, elem, attrs) => {
      setTimeout(() => {
        let p = elem[0].querySelector(".sb-controls");
        let c = p.querySelector("controls")
        if(c) {
          if(c.children.length == 0) { p.style.display = "none"; }
        }
      }, 0);
    }
})
export class SectionboxController {
    getClasses() {
      let color = this.color ? this.color : "blue";
      let collapsed = this.collapsed ? "collapsed" : "";
      return `${color} ${collapsed}`
    }
    collapse() {
      this.collapsed === undefined ? true : this.collapsed;
      this.collapsed = !this.collapsed;
    }
    isModal() {
      return (this.modal != undefined || this.modal === true);
    }
    onTop() {
      return (this.topcontrols != undefined || this.topcontrols === true);
    }
    close() {
      this.onClose()();
    }
}
