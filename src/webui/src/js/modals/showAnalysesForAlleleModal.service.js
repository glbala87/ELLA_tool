/* jshint esnext: true */
import { Service, Inject } from '../ng-decorators'

export class ShowAnalysesForAlleleController {
    constructor(allele, modalInstance, AlleleResource, clipboard, toastr) {
        this.allele = allele
        this.modal = modalInstance
        this.clipboard = clipboard
        this.toastr = toastr
        this.alleleResource = AlleleResource
        this.isAccepted = false
    }

    acceptWarning() {
        this.isAccepted = true
        this.alleleResource.getAnalyses(this.allele.id).then(analyses => {
            this.analyses = analyses
        })
    }

    copyToClipboard() {
        let text = this.allele.toString() + '\n'
        text += this.analyses.map(a => a.name).join('\n')
        this.clipboard.copyText(text)
        this.toastr.info('Copied text to clipboard.', null, 1000)
    }

    getModalColor() {
        return this.isAccepted ? 'blue' : 'red'
    }
}

@Service({
    serviceName: 'ShowAnalysesForAlleleModal'
})
@Inject('$uibModal')
export class ShowAnalysesForAlleleModal {
    constructor($uibModal) {
        this.modalService = $uibModal
    }

    /**
     * Popups a dialog askin if user wants to own the analysis
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with true/false.
     */
    show(allele) {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/showAnalysesForAllele.ngtmpl.html',
            controller: [
                'allele',
                '$uibModalInstance',
                'AlleleResource',
                'clipboard',
                'toastr',
                ShowAnalysesForAlleleController
            ],
            controllerAs: 'vm',
            size: 'lg',
            resolve: {
                allele: () => allele
            },
            backdrop: 'static' // Disallow closing by clicking outside
        })

        return modal.result
    }
}
