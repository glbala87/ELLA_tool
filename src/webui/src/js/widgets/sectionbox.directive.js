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
        collapsible: '=?', // bool: whether box can collapse
        collapsed: '=?',
        onClose: '&',
        color: '@'
    },
    transclude: { title: 'titlebar', contentwrapper: '?contentwrapper', top: '?top' , controls: '?controls' },
    templateUrl: 'ngtmpl/sectionbox.ngtmpl.html',
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
      if (this.isModal() || !this.isCollapsible()) { return; }
      this.collapsed === undefined ? true : this.collapsed;
      this.collapsed = !this.collapsed;
    }

    isCollapsible() {
        return (this.collapsible === undefined || this.collapsible) && !this.isModal();
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
