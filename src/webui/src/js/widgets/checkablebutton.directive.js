/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'checkable-button',
    transclude: {
        checked: 'checked'
    },
    scope: {
        ngModel: '=' // Bit of a hack, but works. Use ngModel for consistant naming
    },
    templateUrl: 'ngtmpl/checkablebutton.ngtmpl.html'
})
export class CheckableButtonController {

    check() {
        this.ngModel = !this.ngModel;
    }

}
