/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class ShowAnalysesForAlleleController {
    constructor(allele, modalInstance, AlleleResource) {
        this.allele = allele;
        this.modal = modalInstance;
        this.alleleResource = AlleleResource;
        this.isAccepted = false;
    }

    acceptWarning() {
        this.isAccepted = true;
        this.alleleResource.getAnalyses(this.allele.id).then(analyses => {
            this.analyses = analyses;
        });
    }

    getModalColor() {
        return this.isAccepted ? 'blue' : 'red';
    }

}


@Service({
    serviceName: 'ShowAnalysesForAlleleModal'
})
@Inject('$uibModal')
export class ShowAnalysesForAlleleModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a dialog askin if user wants to own the analysis
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with true/false.
     */
    show(allele) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/showAnalysesForAllele.ngtmpl.html',
            controller: ['allele', '$uibModalInstance', 'AlleleResource', ShowAnalysesForAlleleController],
            controllerAs: 'vm',
            size: 'lg',
            resolve: {
                allele: () => allele
            }
    });

        return modal.result;
    }

}
