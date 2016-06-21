/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

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
    template: '<textarea ng-disabled="vm.ngDisabled" rows=1 placeholder="{{vm.placeholder}}" ng-model="vm.ngModel"></textarea>',
    link: (scope, elem, attrs) => {
        autosize(elem.children()[0]);
        scope.$watch( () => scope.ngModel, () => autosize.update(elem.children()[0]) );
    }

})
export class AutosizeTextareaController { }
