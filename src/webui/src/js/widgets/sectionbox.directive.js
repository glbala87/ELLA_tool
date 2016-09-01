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
        <div class="close" ng-click="vm.close()" ng-if="vm.isModal()">X</div> \
        <div ng-transclude="titlebar" ng-click="vm.collapse()"></div> \
      </header> \
      <div class="sb-container" ng-class="{topcontrols: vm.onTop()}"> \
        <article class="sb-body" ng-transclude="contentwrapper"></article> \
        <aside class="sb-controls" ng-transclude="controls"></aside> \
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
