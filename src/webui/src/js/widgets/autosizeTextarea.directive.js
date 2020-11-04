/* jshint esnext: true */

import { Directive } from '../ng-decorators'
import autosize from 'autosize'

/**
 <autosize-textarea>
 Autosize textarea element that will automatically resize with user input
 */
@Directive({
    selector: 'autosize-textarea',
    restrict: 'E',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngModelWatch: '=?',
        ngDisabled: '=?',
        ngChange: '&?'
    },
    template:
        '<textarea class="id-autosizeable" ng-disabled="vm.ngDisabled" rows=1 placeholder="{{vm.placeholder}}" ng-model="vm.ngModel" ng-model-watch="vm.ngModelWatch"></textarea>',
    link: (scope, elem, attrs) => {
        let textarea = elem.children()[0]
        autosize(textarea)
        scope.$watch(
            () => scope.ngModel,
            () => {
                // Will not work with ng-change in HTML, probably due to some priority issues
                if (scope.ngChange) {
                    scope.ngChange()
                }
                autosize.update(textarea)
            }
        )
        // when textarea initially is hidden and then shown, we must explicitly autosize it:
        // (http://www.jacklmoore.com/autosize/#faq-hidden)
        setTimeout(() => {
            autosize.update(textarea)
        }, 100)
    }
})
export class AutosizeTextareaController {}
