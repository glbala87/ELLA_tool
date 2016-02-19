/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'card',
    templateUrl: 'ngtmpl/card.ngtmpl.html',
    transclude: {
        topLeft: '?header',
        topRight: '?status',
        content: 'content',
        expanded: '?expanded',
        controls: '?controls'
    },
    scope: {
        options: '=', // {collapsed: bool, expanded: bool}
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

    /**
     * Collapses the whole card area, except the header part.
     */
    collapse() {
        this.options.collapsed = !this.options.collapsed;
    }

}
