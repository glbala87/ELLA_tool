/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';


export class CustomAnnotationController {
    constructor(modalInstance, Config, alleles) {
        this.modal = modalInstance;
        this.config = Config.getConfig();
        this.alleles = alleles;
        this.selected_allele = alleles[0];
        this.selected_annotation_group = Object.keys(this.config.custom_annotation)[0];
        this.custom_annotation = {};
        this.copyAlleleCustomAnnotation();
    }

    getAlleleDisplay(allele) {
        let result = '';
        for (let f of allele.annotation.filtered) {
            result += `${f.SYMBOL} ${f.HGVSc_short}`;
        }
        return result;
    }

    addAnnotation() {
        if (!('custom' in this.custom_annotation)) {
            this.custom_annotation.custom = {};
        }
        this.custom_annotation.custom[this.selected_annotation_group] = this.selected_annotation_value[1];
    }

    getUrl() {
        let gene = this.selected_allele.annotation.filtered[0].SYMBOL;
        let urls = {
            'LOVD': `http://chromium.lovd.nl/LOVD2/home.php?select_db=${gene}`
        };
        if (this.selected_annotation_group in urls) {
            return urls[this.selected_annotation_group];
        }
    }

    copyAlleleCustomAnnotation() {
        if ('custom' in this.selected_allele.annotation) {
            this.custom_annotation.custom = this.selected_allele.annotation.custom;
        }
        else {
            this.custom_annotation = {custom: {}};
        }
    }

    save() {
        this.modal.close({
            allele: this.selected_allele,
            annotation: this.custom_annotation
        });
    }
}


@Service({
    serviceName: 'CustomAnnotationModal'
})
@Inject('$modal', 'CustomAnnotationResource')
export class CustomAnnotationModal {

    constructor($modal, CustomAnnotationResource) {
        this.modalService = $modal;
        this.customAnnotationResource = CustomAnnotationResource;
    }

    /**
     * Popups a dialog for adding custom annotation for one allele
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with true/false.
     */
    show(alleles) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/customAnnotationModal.ngtmpl.html',
            controller: ['$modalInstance', 'Config', 'alleles', CustomAnnotationController],
            controllerAs: 'vm',
            resolve: {
                alleles: () => alleles
            }
        });

        modal.result.then(result => {
            if (result) {
                this.customAnnotationResource.createOrUpdateCustomAnnotation(result.allele.id, result.annotation);
            }
            console.log(result);
        })

        return modal.result;
    }

}
