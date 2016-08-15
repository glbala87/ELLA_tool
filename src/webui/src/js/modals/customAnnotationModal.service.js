/* jshint esnext: true */
import {deepEquals, deepCopy} from '../util';
import {Service, Inject} from '../ng-decorators';

/**
 * Supports two "modes", normal annotation and adding
 * new references. References are seen as type of
 * annotation. Reference mode is triggered when
 * category === 'references'.
 */
export class CustomAnnotationController {
    constructor(modalInstance, Config, ReferenceResource, CustomAnnotationResource, title, alleles, category) {
        this.modal = modalInstance;
        this.category = category;
        this.config = Config.getConfig();
        this.title = title;
        this.alleles = alleles;
        this.selected_allele = alleles[0];
        this.referenceResource = ReferenceResource;
        this.customAnnotationResource = CustomAnnotationResource;
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
        this.references = [];  // Holds reference objects for showing details

        this.setup();
    }

    /**
     * Loads in CustomAnnotation objects from API
     * for all the alleles.
     */
    setup() {
        let allele_ids = this.alleles.map(a => a.id);
        this.customAnnotationResource.getByAlleleIds(allele_ids).then(data => {
            this.existing_custom_annotations = data;

            // Perform initial copy of the existing annotation data,
            // into our custom_annotation model.
            for (let allele of this.alleles) {
                this.custom_annotation[allele.id] = this.getExistingCustomAnnotation(allele);
            }

            if (this.category === 'references') {
                this._loadReferences();
            }
        });

    }

    /**
     * Returns valid group options given the selected Allele.
     * If a group is only valid for a set of genes, the genes relevant for the Allele
     * in question checked.
     * @return {Array(object)} List of group objects
     */
    getAnnotationGroups() {
        let valid_groups = this.config.custom_annotation[this.category].filter(c => {
            if ('only_for_genes' in c) {
                let genes = this.selected_allele.annotation.filtered.map(t => t.SYMBOL);
                return c.only_for_genes.some(g => genes.includes(g));
            }
            // If no restriction, always include it.
            return true;
        });

        // Select first option by default if not already selected
        if (!valid_groups.includes(this.selected_annotation_group)) {
            this.selected_annotation_group = valid_groups[0];
        }
        return valid_groups;
    }

    /**
    * Tries to get any existing CustomAnnotation for the allele in question
    * and returns a copy of it. If no CustomAnnotation is present, an empty object is returned.
    * @param  {Allele} allele Allele for which to look for existing CustonAnnotation
    * @return {Object}        Copy of existing CustomAnnotation, or new empty object
    */
    getExistingCustomAnnotation(allele) {
        let existing = this.existing_custom_annotations.find(e => e.allele_id === allele.id);
        if (existing) {
            return deepCopy(existing.annotations);
        }
        return {};
    }


    /**
     * Convenience function.
     * Fetches the data object for the currently selected allele and category.
     * If there's no data, create an empty structure for current category.
     *
     * Expects this.existing_custom_annotations to be loaded from API already
     * (see setup())
     * @return {Object/Array} Array if category === 'references', otherwise Object
     */
    getCurrent() {
        if (!this.existing_custom_annotations) {
            return;
        }
        if (!(this.selected_allele.id in this.custom_annotation)) {
            this.custom_annotation[this.selected_allele.id] = this.getExistingCustomAnnotation(this.selected_allele);
        }
        if (!(this.category in this.custom_annotation[this.selected_allele.id])) {
            if (this.category === 'references') {
                this.custom_annotation[this.selected_allele.id].references = [];
            }
            else {
                this.custom_annotation[this.selected_allele.id][this.category] = {};
            }
        }
        return this.custom_annotation[this.selected_allele.id][this.category];
    }

    /**
     * Returns whether there are any added annotations.
     * @return {Boolean}
     */
    hasAddedAnnotations() {
        let current = this.getCurrent();
        if (current) {
            if (this.category === 'references') {
                return current.length > 0;
            }
            else {
                return Object.keys(current).length > 0;
            }
        }
        return false;
    }

    formatAllele(allele) {
        let result = '';
        for (let f of allele.annotation.filtered) {
            result += `${f.SYMBOL} ${f.HGVSc_short}`;
        }
        return result;
    }

    addAnnotation() {
        if (Array.isArray(this.selected_annotation_value)) {
            this.getCurrent()[this.selected_annotation_group.key] = this.selected_annotation_value[1];
        }
        else {
            this.getCurrent()[this.selected_annotation_group.key] = this.selected_annotation_value;
        }
    }

    /**
     * Loads references from the API into this.references
     * to get reference details to show in the UI.
     */
    _loadReferences() {
        let pmids = [];
        for (let [allele_id, data] of Object.entries(this.custom_annotation)) {
            if ('references' in data) {
                pmids = pmids.concat(data.references.map(r => r.pubmed_id));
            }
        }
        console.log(pmids);
        this.referenceResource.getByPubMedIds(pmids).then(refs => {
            this.references = refs;
        });
    }

    getReference(pmid) {
        return this.references.find(r => r.pubmed_id === pmid);
    }

    _addReferenceToAnnotation(pubmed_id) {
        let existing = this.getCurrent().find(r => r.pubmed_id === pubmed_id);
        if (!existing) {
            this.getCurrent().push({
                pubmed_id: pubmed_id,
                sources: ['User']
            });
        }
    }

    addReference() {
        this.referenceResource.createFromXml(this.reference_xml).then(ref => {
            this.reference_error = false;
            this._addReferenceToAnnotation(ref.pubmed_id);
            this.reference_xml = '';
            this._loadReferences();  // Reload list of references to reflect possible changes
        }).catch(() => {
            this.reference_error = true;
        });
    }

    /**
     * Looks for whether there are any URLs for the selected annotation group.
     * @return {Array(string)}       URLs
     */
    getUrls() {
        if (!this.selected_annotation_group) {
            return [];
        }

        let genes = this.selected_allele.annotation.filtered.map(t => t.SYMBOL);

        let urls = [];
        if ('url_for_genes' in this.selected_annotation_group) {
            for (let gene of genes) {
                if (gene in this.selected_annotation_group.url_for_genes) {
                    urls.push(this.selected_annotation_group.url_for_genes[gene]);
                }
            }
        }
        if ('url' in this.selected_annotation_group) {
            urls.push(this.selected_annotation_group.url);
        }
        return urls;
    }

    removeReference(ref) {
        this.custom_annotation[this.selected_allele.id].references = this.getCurrent().filter(r => {
            return ref.pubmed_id !== r.pubmed_id;
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
                let existing = this.getExistingCustomAnnotation(allele);
                // If data hasn't changed, remove it from list of changes
                if (deepEquals(this.custom_annotation[allele.id], existing)) {
                    delete this.custom_annotation[allele.id];
                }
            }
        }
        this.modal.close(this.custom_annotation);
    }
}


@Service({
    serviceName: 'CustomAnnotationModal'
})
@Inject('$uibModal', 'CustomAnnotationResource')
export class CustomAnnotationModal {

    constructor($uibModal, CustomAnnotationResource) {
        this.modalService = $uibModal;
        this.customAnnotationResource = CustomAnnotationResource;
    }

    /**
     * Popups a dialog for adding custom annotation for one allele
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with result data from dialog.
     */
    show(title, alleles, category) {

        if (!category) {
            category = 'external';
        }

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/customAnnotationModal.ngtmpl.html',
            controller: ['$uibModalInstance', 'Config', 'ReferenceResource', 'CustomAnnotationResource', 'title', 'alleles', 'category', CustomAnnotationController],
            controllerAs: 'vm',
            resolve: {
                title: () => title,
                alleles: () => alleles,
                category: () => category
            }
        });

        return modal.result.then(custom_annotation => {
            for (let allele_id of Object.keys(custom_annotation)) {
                this.customAnnotationResource.createOrUpdateCustomAnnotation(allele_id, custom_annotation[allele_id]);
            }
            return custom_annotation;
        });

    }

}
