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
        ngModel: '='
    },
    template: '<textarea rows=1 class="comment" placeholder="{{vm.placeholder}}" ng-model="vm.ngModel">LOL</textarea>',
    link: (scope, elem, attrs) => {
      autosize(elem.children()[0]);
      scope.$watch( () => scope.ngModel, () => autosize.update(elem.children()[0]) );
    }
})
export class AutosizeTextareaController { }
