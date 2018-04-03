/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('showAnalysesForAllele', {
    templateUrl: 'ngtmpl/showAnalysesForAllele.ngtmpl.html',
    controller: connect(
        {
            analyses: state`modals.showAnalysesForAllele.data.analyses`,
            allele: state`modals.showAnalysesForAllele.allele`,
            showAnalysesForAlleleAccepted: signal`modals.showAnalysesForAlleleAccepted`,
            copyAnalysesForAlleleClicked: signal`modals.copyAnalysesForAlleleClicked`,
            closeClicked: signal`closeModal`
        },
        'ShowAnalysesForAllele',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getColor() {
                        return $ctrl.accepted ? 'blue' : 'red'
                    },
                    isAccepted() {
                        return $ctrl.accepted || false
                    },
                    accept() {
                        $ctrl.accepted = true
                        $ctrl.showAnalysesForAlleleAccepted({ alleleId: $ctrl.allele.id })
                    },
                    close() {
                        $ctrl.closeClicked({ modalName: 'showAnalysesForAllele' })
                    }
                })
            }
        ]
    )
})

/*
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

*/
