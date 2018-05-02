/* jshint esnext: true */
import { deepEquals, deepCopy } from '../util'
import { Service, Inject } from '../ng-decorators'

/**
 * Supports two "modes", normal annotation and adding
 * new references. References are seen as type of
 * annotation. Reference mode is triggered when
 * category === 'references'.
 */

export class CustomAnnotationController {
    constructor(
        $scope,
        modalInstance,
        Config,
        ReferenceResource,
        CustomAnnotationResource,
        title,
        placeholder,
        allele,
        category
    ) {
        this.scope = $scope
        this.modal = modalInstance
        this.category = category
        this.config = Config.getConfig()
        this.title = title
        this.placeholder = placeholder
        this.allele = allele
        this.referenceResource = ReferenceResource
        this.customAnnotationResource = CustomAnnotationResource

        // custom_annotation structure example:
        // {
        //      external: {  //category
        //          somekey: 'somevalue'
        //    }
        // }
        //
        this.custom_annotation = {}

        // Reference specific
        this.reference_xml = '' // Holds user pasted xml
        this.reference_error = false
        this.references = [] // Holds reference objects for showing details

        this.referenceModes = ['Search', 'PubMed', 'Manual']
        this.referenceMode = this.referenceModes[0]
        this.referencePublishStatuses = ['Published', 'Unpublished']
        this.referencePublishStatus = this.referencePublishStatuses[1]
        this.referenceSearchPhrase = ''
        this.referenceSearchResults = []

        this.resetManualReference(false)

        if (this.category === 'references') {
            $scope.$watch(
                () => this.referenceSearchPhrase,
                () => {
                    this.referenceResource.search(this.referenceSearchPhrase).then((results) => {
                        this.referenceSearchResults = results
                    })
                }
            )
        }

        this.setup()
    }

    resetManualReference(published) {
        this.manualReference = {
            authors: '',
            title: '',
            journal: '',
            volume: '',
            issue: '',
            year: '',
            pages: '',
            abstract: '',
            published: published
        }
    }

    /**
     * Loads in CustomAnnotation objects from API
     * for all the allele.
     */
    setup() {
        this.customAnnotationResource.getByAlleleIds([this.allele.id]).then((data) => {
            this.existing_custom_annotations = data

            // Perform initial copy of the existing annotation data,
            // into our custom_annotation model.
            this.custom_annotation = this.getExistingCustomAnnotation()

            if (this.category === 'references') {
                this._loadReferences()
            }
        })
    }

    /**
     * Returns valid group options given the selected Allele.
     * If a group is only valid for a set of genes, the genes relevant for the Allele
     * in question checked.
     * @return {Array(object)} List of group objects
     */
    getAnnotationGroups() {
        let valid_groups = this.config.custom_annotation[this.category].filter((c) => {
            if ('only_for_genes' in c) {
                let hgnc_ids = this.allele.annotation.filtered.map((t) => t.hgnc_id)
                return c.only_for_genes.some((g) => hgnc_ids.includes(g))
            }
            // If no restriction, always include it.
            return true
        })

        return valid_groups
    }

    /**
     * Tries to get any existing CustomAnnotation for the allele in question
     * and returns a copy of it. If no CustomAnnotation is present, an empty object is returned.
     * @param  {Allele} allele Allele for which to look for existing CustonAnnotation
     * @return {Object}        Copy of existing CustomAnnotation, or new empty object
     */
    getExistingCustomAnnotation() {
        let existing = this.existing_custom_annotations.find((e) => e.allele_id === this.allele.id)
        if (existing) {
            return deepCopy(existing.annotations)
        }
        return {}
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
            return
        }

        if (!(this.category in this.custom_annotation)) {
            if (this.category === 'references') {
                this.custom_annotation.references = []
            } else {
                this.custom_annotation[this.category] = {}
            }
        }
        return this.custom_annotation[this.category]
    }

    formatAllele(allele) {
        let result = ''
        for (let f of allele.annotation.filtered) {
            result += `${f.symbol} ${f.HGVSc_short || allele.getHGVSgShort()}`
        }
        return result
    }

    /**
     * Loads references from the API into this.references
     * to get reference  details to show in the UI.
     */
    _loadReferences() {
        let ids = []
        if ('references' in this.custom_annotation) {
            ids = this.custom_annotation.references.map((r) => r.id)
        }
        this.referenceResource.getByIds(ids).then((refs) => {
            this.references = refs
        })
    }

    getReference(id) {
        return this.references.find((r) => r.id === id)
    }

    _addReferenceToAnnotation(id, pubmed_id) {
        let existing = this.getCurrent().find((r) => r.id === id && r.pubmed_id === pubmed_id)
        if (!existing) {
            this.getCurrent().push({
                id: id,
                pubmed_id: pubmed_id,
                sources: ['User']
            })
        }
    }

    addReference(reference) {
        if (this.referenceMode === this.referenceModes[0]) {
            // Search
            this._addReferenceToAnnotation(reference.id, reference.pubmed_id)
            this._loadReferences()
        } else if (this.referenceMode === this.referenceModes[1]) {
            // PubMed XML
            this.referenceResource
                .createFromXml(this.reference_xml)
                .then((ref) => {
                    this.reference_error = false
                    this._addReferenceToAnnotation(ref.id, ref.pubmed_id)
                    this.reference_xml = ''
                    this._loadReferences() // Reload list of references to reflect possible changes
                })
                .catch(() => {
                    this.reference_error = true
                })
        } else if (this.referenceMode === this.referenceModes[2]) {
            // Manual
            this.referenceResource
                .createFromManual(this.manualReference)
                .then((ref) => {
                    this.reference_error = false
                    this._addReferenceToAnnotation(ref.id, ref.pubmed_id)
                    this.resetManualReference(this.manualReference.published)
                    this._loadReferences()
                })
                .catch(() => {
                    this.reference_error = true
                })
        }
    }

    canAddManualReference() {
        return !(
            this.manualReference.title.length &&
            this.manualReference.authors.length &&
            this.manualReference.journal.length &&
            this.manualReference.year.length
        )
    }

    /**
     * Looks for whether there are any URLs for provided annotation group.
     * @return {Array(string)}       URLs
     */
    getUrls(group) {
        let hgnc_ids = this.allele.annotation.filtered.map((t) => t.hgnc_id)
        let urls = new Set()
        if ('url_for_genes' in group) {
            for (let hgnc_id of hgnc_ids) {
                // json data has string keys
                if (hgnc_id.toString() in group.url_for_genes) {
                    urls.add(group.url_for_genes[hgnc_id])
                }
            }
        }
        if ('url' in group) {
            urls.add(group.url)
        }

        return Array.from(urls)
    }

    removeReference(ref) {
        this.custom_annotation.references = this.getCurrent().filter((r) => {
            return ref.id !== r.id
        })
    }

    save() {
        if (this.category === 'external' || this.category === 'prediction') {
            for (let [key, value] of Object.entries(this.custom_annotation[this.category])) {
                if (value === null) {
                    delete this.custom_annotation[this.category][key]
                }
            }
        }
        this.modal.close(this.custom_annotation)
    }
}

@Service({
    serviceName: 'CustomAnnotationModal'
})
@Inject('$uibModal', 'CustomAnnotationResource')
export class CustomAnnotationModal {
    constructor($uibModal, CustomAnnotationResource) {
        this.modalService = $uibModal
        this.customAnnotationResource = CustomAnnotationResource
    }

    /**
     * Popups a dialog for adding custom annotation for one allele
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with result data from dialog.
     */
    show(title, placeholder, allele, category) {
        if (!category) {
            category = 'external'
        }

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/customAnnotationModal.ngtmpl.html',
            controller: [
                '$scope',
                '$uibModalInstance',
                'Config',
                'ReferenceResource',
                'CustomAnnotationResource',
                'title',
                'placeholder',
                'allele',
                'category',
                CustomAnnotationController
            ],
            controllerAs: 'vm',
            size: 'lg',
            resolve: {
                title: () => title,
                placeholder: () => placeholder,
                allele: () => allele,
                category: () => category
            }
        })
        // our modal UI calls the close method on the modal instance (save, cancel and the X in the corner),
        // which triggers the 'then' callback, with or without data.
        return modal.result.then(
            (custom_annotation) => {
                if (!custom_annotation) return
                return this.customAnnotationResource
                    .createOrUpdateCustomAnnotation(allele.id, custom_annotation)
                    .then(() => {
                        return custom_annotation
                    })
            },
            () => console.log('modal dismissed')
        )
    }
}
