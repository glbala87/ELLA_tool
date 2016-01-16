/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';


/**
 * Supports two "modes", normal annotation and adding
 * new references. References are seen as type of
 * annotation. Reference mode is triggered when
 * category === 'references'.
 */
export class CustomAnnotationController {
    constructor(modalInstance, Config, ReferenceResource, alleles, category) {
        this.modal = modalInstance;
        this.category = category;
        this.config = Config.getConfig();
        this.alleles = alleles;
        this.selected_allele = alleles[0];
        this.referenceResource = ReferenceResource;
        if (this.category in this.config.custom_annotation) {
            this.selected_annotation_group = Object.keys(this.config.custom_annotation[this.category])[0];
        }

        // custom_annotation structure example:
        // {
        //      '1': {  // allele_id
        //          external: {  //category
        //              somekey: 'somevalue'
        //          }
        //      }
        // }
        //
        this.custom_annotation = {};

        // Reference specific
        this.reference_xml = ''; // Holds user pasted xml
        this.reference_error = false;
    }

    /**
     * Convenience function.
     * Fetches the data object for the currently selected allele and category.
     * @return {Object/Array} Array if category === 'references', otherwise Object
     */
    getCurrent() {
        if (!(this.selected_allele.id in this.custom_annotation)) {
            this.custom_annotation[this.selected_allele.id] = this.getAlleleCustomAnnotation(this.selected_allele);
        }
        return this.custom_annotation[this.selected_allele.id][this.category];
    }

    getAlleleDisplay(allele) {
        let result = '';
        for (let f of allele.annotation.filtered) {
            result += `${f.SYMBOL} ${f.HGVSc_short}`;
        }
        return result;
    }

    addAnnotation() {
        this.getCurrent()[this.selected_annotation_group] = this.selected_annotation_value[1];
    }

    _addReferenceToAnnotation(pubmedID) {
        let existing = this.getCurrent().find(r => r.pubmedID === pubmedID);
        if (!existing) {
            this.getCurrent().push({
                pubmedID,
                sources: ['User']
            });
        }
    }

    addReference() {
        this.referenceResource.createFromXml(this.reference_xml).then(ref => {
            this.reference_error = false;
            this._addReferenceToAnnotation(ref.pubmedID);
            this.reference_xml = '';
        }).catch(() => {
            this.reference_error = true;
        });
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

    getAlleleCustomAnnotation(allele) {
        let data = {};
        // Treat 'references' as special case
        // This is a bit hacky as we don't have access to original
        // custom_annotation object, but should work fine
        let existing = this.selected_allele.annotation.references.filter(r => {
            console.log("ASDASDAS", r);
            if ('sources' in r) {
                return r.sources.includes('User');
            }
            return false;
        });
        data.references = existing || [];

        // Process other types of custom annotation
        for (let category of Object.keys(this.config.custom_annotation)) {
            if (!(category in data)) {
                data[category] = {};
            }
            for (let k of Object.keys(this.config.custom_annotation[category])) {
                if (category in this.selected_allele.annotation &&
                    k in this.selected_allele.annotation[category]) {
                    data[category][k] = this.selected_allele.annotation[category][k];
                }
            }
        }
        return data;
    }

    removeReference(ref) {
        this.custom_annotation[this.selected_allele.id].references = this.getCurrent().filter(r => {
            return ref.pubmedID !== r.pubmedID;
        });
    }

    removeEntry(key) {
        delete this.getCurrent()[key];
    }

    save() {
        // Clean up data before storing.
        // Compare new data against existing custom_annotation,
        // and remove if the allele's existing custom_annotation is
        // lacking or same as new one.

        for (let allele of this.alleles) {
            if (allele.id in this.custom_annotation) {
                // If data hasn't changed, remove it
                let existing = this.getAlleleCustomAnnotation(allele);
                console.log(existing);
                console.log(this.custom_annotation[allele.id][this.category]);
                if (JSON.stringify(this.custom_annotation[allele.id][this.category]) == JSON.stringify(existing)) {
                    delete this.custom_annotation[allele.id];
                }
            }
        }
        console.log(this.custom_annotation);
        this.modal.close(this.custom_annotation);
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
            controller: ['$modalInstance', 'Config', 'ReferenceResource', 'alleles', 'category', CustomAnnotationController],
            controllerAs: 'vm',
            resolve: {
                alleles: () => alleles,
                category: () => category
            }
        });

        modal.result.then(custom_annotation => {
            for (let allele_id of Object.keys(custom_annotation)) {
                this.customAnnotationResource.createOrUpdateCustomAnnotation(allele_id, custom_annotation[allele_id]);
            }
        })

        return modal.result;
    }

}
