/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

/**
 * Use inside a ng-repeat to inform the template if our list has only one element.
 * The property 'singleElement' is set to true if our list has only one element
 */

@Directive({
    selector: 'repeat-wrapper',
    transclude: true,
    templateUrl: function(element, attr) {
        return attr.templateUrl ? attr.templateUrl : 'ngtmpl/repeatWrapper.ngtmpl.html'
    },
    scope: {
        item: '=',
        templateUrl: '=?'
    }
})
@Inject('$scope')
export class TranscriptWrapperController {
    constructor($scope) {
        /*
           Really hacky way to detect if directive is used in a ng-repeat and
           there's just one item.
        */
        this.singleElement = !($scope.$parent.$index === 0 && $scope.$parent.$last)
    }
}
