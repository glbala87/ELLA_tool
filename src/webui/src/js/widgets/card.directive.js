/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'card',
    templateUrl: 'ngtmpl/card.ngtmpl.html',
    transclude: {
        topLeft: '?header',
        topRight: '?status',
        content: 'content',
        expanded: 'expanded',
        controls: '?controls'
    },
    scope: {
        color: '@',
        expanded: '@',
        collapsed: '@'
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
        this.expanded = !this.expanded;
    }

    /**
     * Collapses the whole card area, except the header part.
     */
    collapse() {
        this.collapsed = !this.collapsed;
    }

}
