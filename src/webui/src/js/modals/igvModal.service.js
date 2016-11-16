/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class IgvModalController {
    /**
     * Controller for showing IGV.js in a modal
     */

    constructor(modalInstance, analysis, allele) {

        let padding = 50;

        let tracks = []
        // Not working correctly...
        /*tracks.push({
            type: 'variant',
            url: `api/v1/analyses/${analysis.id}/vcf/`,
            indexURL: `api/v1/analyses/${analysis.id}/vcf/?index=true`,
            name: 'Variants'
        });*/
        tracks.push({
            name: 'Gencode',
            url: 'api/v1/igv/gencode.v18.collapsed.bed',
            displayMode: 'EXPANDED'
        });
        for (let sample of analysis.samples) {
            tracks.unshift({
                type: 'alignment',
                height: 400,
                url: `api/v1/analyses/${analysis.id}/bams/${sample.id}/`,
                indexURL: `api/v1/analyses/${analysis.id}/bams/${sample.id}/?index=true`,
                name: sample.identifier
            });
        }
        this.options = {tracks};
        this.chrom = `${allele.chromosome}`;
        this.pos = `${allele.start_position}`;
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
                'analysis',
                'allele',
                IgvModalController
            ],
            controllerAs: 'vm',
            resolve: {
                'analysis': () => analysis,
                'allele': () => allele
            },
            size: 'lg'
        });

        return modal.result;

    }

}
