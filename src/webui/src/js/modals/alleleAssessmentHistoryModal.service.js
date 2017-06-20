/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class AlleleAssessmentHistoryController {
    constructor(modalInstance, alleleResource, alleleAssessmentResource, attachmentResource, allele_id) {
        this.modal = modalInstance;
        this.allele_id = allele_id;
        this.alleleResource = alleleResource;
        this.alleleAssessmentResource = alleleAssessmentResource;
        this.attachmentResource = attachmentResource;

        this.loadData();
    }

    loadData() {
        this.alleleAssessmentResource.getHistoryForAlleleId(this.allele_id).then(aas => {
            this.alleleassessments = aas;
            let attachment_ids = this.alleleassessments.map((aa) => aa.attachment_ids).reduce((a,b) => a.concat(b))
            attachment_ids = Array.from(new Set(attachment_ids))
            let attachments = {};
            this.attachmentResource.getByIds(attachment_ids).then((a) => {
                for (let atchmt of a) {
                    attachments[atchmt.id] = atchmt;
                }
                this.attachments = attachments;
            })
        })
        this.alleleResource.get([this.allele_id]).then(alleles => {
            this.allele = alleles[0];
        })
    }
}


@Service({
    serviceName: 'AlleleAssessmentHistoryModal'
})
@Inject('$uibModal')
export class AlleleAssessmentHistoryModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a modal for showing classification/alleleassessment history
     * @param  {int} allele_id Allele id for which to show history
     * @return {Promise} Promise that resolves when dialog is closed.
     */
    show(allele_id) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/alleleAssessmentHistoryModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                'AlleleResource',
                'AlleleAssessmentResource',
                'AttachmentResource',
                'allele_id',
                AlleleAssessmentHistoryController
            ],
            controllerAs: 'vm',
            resolve: {
                'allele_id': () => allele_id,
            },
            size: 'lg'
        });

        return modal.result;

    }

}
