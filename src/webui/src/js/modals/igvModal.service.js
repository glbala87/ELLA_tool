/* jshint esnext: true */
import { Service, Inject } from '../ng-decorators'

export class IgvModalController {
    /**
     * Controller for showing IGV.js in a modal
     */

    constructor(modalInstance, Config, allele) {
        let config = Config.getConfig()

        let padding = 50

        let tracks = []

        tracks.push({
            name: 'Gencode',
            url: config.igv.tracks.gencode,
            displayMode: 'EXPANDED'
        })
        for (let sample of allele.samples) {
            tracks.unshift({
                type: 'alignment',
                height: 400,
                url: `api/v1/samples/${sample.id}/bams/`,
                indexURL: `api/v1/samples/${sample.id}/bams/?index=true`,
                name: sample.identifier
            })
        }
        let reference = {
            id: 'GRCh37',
            fastaURL: config.igv.reference.fastaURL,
            cytobandURL: config.igv.reference.cytobandURL
        }
        this.options = {
            tracks,
            reference
        }
        this.chrom = `${allele.chromosome}`
        this.pos = `${allele.start_position}`
        this.modal = modalInstance
    }
}

@Service({
    serviceName: 'IgvModal'
})
@Inject('$uibModal')
export class IgvModal {
    constructor($uibModal) {
        this.modalService = $uibModal
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
            controller: ['$uibModalInstance', 'Config', 'allele', IgvModalController],
            controllerAs: 'vm',
            resolve: {
                allele: () => allele
            },
            size: 'lg'
        })

        return modal.result
    }
}
