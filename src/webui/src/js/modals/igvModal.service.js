/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class IgvModalController {
    /**
     * Controller for showing IGV.js in a modal
     */

    constructor(modalInstance) {
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'IgvModal'
})
@Inject('$uibModal')
export class IgvModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a modal for showing IGV.
     * @param  {Analysis} Analysis with data to show (used to get bam info)
     * @param  {Allele} Allele with data to show
     * @return {Promise} Promise that resolves when dialog is closed.
     */
    show(analysis, allele) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/igvModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                IgvModalController
            ],
            controllerAs: 'vm',
            resolve: {
            },
            size: 'lg'
        });

        return modal.result;

    }

}
