import { Directive, Inject } from '../ng-decorators'

// Prevent the click event from propagating to parents. Consider the click handled by the current element.
// http://stackoverflow.com/questions/20300866/angularjs-ng-click-stoppropagation/34746964#34746964

@Directive({
    selector: 'isolateClick',
    restrict: 'AE', // don't work without it
    link: function(scope, elem, attrs) {
        elem.on('click', function(event) {
            event.stopPropagation()
        })
    }
})
export class IsolateClickController {
    constructor() {}
}
