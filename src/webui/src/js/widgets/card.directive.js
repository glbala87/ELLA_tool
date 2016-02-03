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
        expanded: '@'
    }
})
@Inject('$transclude')
export class CardController {

    constructor($transclude) {
        // Collapse card-controls if no content
        this.controlscollapse = !$transclude.isSlotFilled('controls');
    }

    expand() {
        this.expanded = this.expanded === 'true' ? 'false' : 'true';
    }

}
