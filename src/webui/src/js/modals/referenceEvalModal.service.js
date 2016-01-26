/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class ReferenceEvalModalController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(modalInstance,
                allele,
                reference,
                referenceAssessment) {
        this.modal = modalInstance;
        this.allele = allele;
        this.reference = reference;
        this.referenceAssessment = referenceAssessment;
    }

}

@Service({
    serviceName: 'ReferenceEvalModal'
})
@Inject('$uibModal')
export class ReferenceEvalModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a dialog for doing reference evaluation
     * @param  {Allele} Allele for reference evaluation
     * @param  {Reference} Reference to be evaluated
     * @param  {Object} Data for reference assessment
     * @return {Promise} Promise that resolves when dialog is closed.
     */
    show(allele, reference, referenceAssessment) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/referenceEvalModal.ngtmpl.html',
            controller: ['$uibModalInstance', 'allele', 'reference', 'referenceAssessment', ReferenceEvalModalController],
            controllerAs: 'vm',
            resolve: {
                allele: () => allele,
                reference: () => reference,
                referenceAssessment: () => referenceAssessment,
            },
            size: 'lg'
        });

        return modal.result;

    }

}
