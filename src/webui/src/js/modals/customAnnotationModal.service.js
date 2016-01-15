/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';


export class CustomAnnotationController {
    constructor(modalInstance, Config, alleles, category) {
        this.modal = modalInstance;
        this.category = category;
        this.config = Config.getConfig();
        this.alleles = alleles;
        this.selected_allele = alleles[0];
        this.selected_annotation_group = Object.keys(this.config.custom_annotation[this.category])[0];
        this.custom_annotation = {
            [this.category]: {}
        };
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
        if (!(this.category in this.custom_annotation)) {
            this.custom_annotation[this.category] = {};
        }
        this.custom_annotation[this.category][this.selected_annotation_group] = this.selected_annotation_value[1];
    }

    getUrl(group) {
        let gene = this.selected_allele.annotation.filtered[0].SYMBOL;

        if (this.category in this.config.custom_annotation_url &&
            this.selected_annotation_group in this.config.custom_annotation_url[this.category]) {
            let url_match = this.config.custom_annotation_url[this.category][this.selected_annotation_group].find(obj => {
                return obj.gene === gene;
            });
            if (url_match) {
                return url_match.url;
            }
        }
    }

    copyAlleleCustomAnnotation() {
        if (this.category in this.selected_allele.annotation) {
            for (let k of Object.keys(this.config.custom_annotation[this.category])) {
                if (k in this.selected_allele.annotation[this.category]) {
                    this.custom_annotation[this.category][k] = this.selected_allele.annotation[this.category][k];
                }
            }
        }
    }

    removeEntry(key) {
        delete this.custom_annotation[this.category][key];
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
    show(alleles, category) {

        if (!category) {
            category = 'external';
        }

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/customAnnotationModal.ngtmpl.html',
            controller: ['$modalInstance', 'Config', 'alleles', 'category', CustomAnnotationController],
            controllerAs: 'vm',
            resolve: {
                alleles: () => alleles,
                category: () => category
            }
        });

        modal.result.then(result => {
            if (result !== null) {
                this.customAnnotationResource.createOrUpdateCustomAnnotation(result.allele.id, result.annotation);
            }
        })

        return modal.result;
    }

}
