/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'card',
    templateUrl: 'ngtmpl/card.ngtmpl.html',
    transclude: {
        primary: '?primary',
        secondary: '?secondary',
        bottom: 'bottom',
        expanded: '?expanded',
        controls: '?controls'
    },
    scope: {
        options: '=', // {collapsed: bool, expanded: bool}
        collapsible: '=?', // bool: whether card can collapse
        modal: '=?', // bool: whether card is part of a modal
        color: '@'
    }
})
@Inject('$transclude')
export class CardController {

    constructor($transclude) {
        this.hasexpand = $transclude.isSlotFilled('expanded');
        // Collapse card-controls if no content to show there
        this.controlscollapse = !$transclude.isSlotFilled('controls') &&
                                !this.hasexpand;
    }

    /**
     * Expands the <expanded> section
     */
    expand() {
        this.options.expanded = !this.options.expanded;
    }

    isCollapsible() {
        return this.collapsible === undefined || this.collapsible;
    }

    isModal() {
        return this.modal != undefined || this.modal;
    }

    /**
     * Collapses the whole card area, except the header part.
     */
    collapse() {
        if (this.isCollapsible()) {
            this.options.collapsed = !this.options.collapsed;
        }
    }

}
