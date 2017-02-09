
import {Directive} from '../ng-decorators';

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
export class ReferenceAssessment {}
