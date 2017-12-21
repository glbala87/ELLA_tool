import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-reference-detail',
    templateUrl: 'ngtmpl/alleleInfoReferenceDetail.ngtmpl.html',
    scope: {
        reference: '=',
        vm: '='
    },
    replace: true
})
@Inject('$scope')
export class AlleleInfoReferenceDetail {}

