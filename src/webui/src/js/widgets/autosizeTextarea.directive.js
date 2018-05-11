/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

/**
 <autosize-textarea>
 Autosize textarea element that will automatically resize with user input
 */
@Directive({
    selector: 'autosize-textarea',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '=?'
    },
    template:
        '<textarea class="id-autosizeable" ng-disabled="vm.ngDisabled" rows=1 placeholder="{{vm.placeholder}}" ng-model="vm.ngModel"></textarea>',
    link: (scope, elem, attrs) => {
        let textarea = elem.children()[0]
        autosize(textarea)
        scope.$watch(() => scope.ngModel, () => autosize.update(textarea))
        // when textarea initially is hidden and then shown, we must explicitly autosize it:
        // (http://www.jacklmoore.com/autosize/#faq-hidden)
        setTimeout(() => {
            autosize.update(textarea)
        }, 100)
    }
})
export class AutosizeTextareaController {}
