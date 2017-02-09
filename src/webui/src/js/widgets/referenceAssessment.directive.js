
import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

/***
 * Display (some of) a reference assessment
 */

@Directive({
    selector: 'referenceassessment',
    scope: {
        referenceassessment: '='
    },
    templateUrl: 'ngtmpl/referenceAssessment.ngtmpl.html'
})

export class ReferenceAssessment {
    constructor() {}

}
