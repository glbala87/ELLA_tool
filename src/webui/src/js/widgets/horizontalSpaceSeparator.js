import { Directive } from '../ng-decorators'

@Directive({
    selector: 'horizontal-space-separator',
    restrict: 'AE',
    link: function(scope, elem) {
        if (scope.$parent.$index != 0) {
            elem.prepend(',&nbsp;')
        }
    }
})
export class HorizontalSpaceSeparator {
    constructor() {}
}
