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
@Inject('$modal')
export class InterpretationOverrideModal {

    constructor($modal) {
        this.modalService = $modal;
    }

    /**
     * Popups a dialog for adding excluded alleles
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with true/false.
     */
    show() {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationOverride.ngtmpl.html',
            controller: ['$modalInstance', InterpretationOverrideController],
            controllerAs: 'vm',
            resolve: {}
        });

        return modal.result;
    }

}
