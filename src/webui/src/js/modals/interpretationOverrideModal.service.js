/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class InterpretationOverrideController {
    constructor(modalInstance) {
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'InterpretationOverrideModal'
})
@Inject('$uibModal')
export class InterpretationOverrideModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a dialog askin if user wants to own the analysis
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with true/false.
     */
    show() {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationOverrideModal.ngtmpl.html',
            controller: ['$uibModalInstance', InterpretationOverrideController],
            controllerAs: 'vm',
            size: 'lg',
            resolve: {}
        });

        return modal.result;
    }

}
