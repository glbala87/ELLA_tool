/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class AddExcludedAllelesController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(modalInstance,
                Config,
                Allele,
                excluded_allele_ids,
                included_allele_ids,
                sample_id,
                gp_name,
                gp_version) {
        this.modal = modalInstance;
        this.frequencies = Config.getConfig().frequencies;
        this.alleleService = Allele;
        this.included_allele_ids = included_allele_ids;  // Alleles added by user
        this.alleles = {
            class1: [],
            intronic: []
        }; // Alleles loaded from backend
        this.excluded_allele_ids = excluded_allele_ids;
        this.category_excluded_alleles = []; // Alleles filtered on the category, but no further filtering. Needed for showing genes
        this.filtered_alleles = [];  // Finished filtered Alleles to show, that are not yet added
        this.included_alleles = [];  // Alleles added by user (internal use)
        this.category = 'all';
        this.slice = []; // Holds the slice of alleles for pagination
        this.gene_options = []; // Options for gene selection dropdown
        this.selected_gene = null;
        this.page_idx = 1;
        this.number_per_page = 5;

        this.loadAlleles(sample_id, gp_name, gp_version);
    }

    /**
     * Load in all allele data from backend (yes, all x hundreds at once, we're lazy...)
     * TODO: Improve performance with pagination if necessary
     */
    loadAlleles(sample_id, gp_name, gp_version) {

        // Class 1
        let p_class1 = this.alleleService.getAlleles(
            this.excluded_allele_ids.class1,
            sample_id,
            gp_name,
            gp_version
        ).then(alleles => this.alleles.class1 = alleles);

        // Intronic
        let p_intronic = this.alleleService.getAlleles(
            this.excluded_allele_ids.intronic,
            sample_id,
            gp_name,
            gp_version
        ).then(alleles => this.alleles.intronic = alleles);

        // When done, update view data
        Promise.all([p_class1, p_intronic]).then(
            () => this.update()
        )
    }

    update() {
        this._updateFilter();
        this._updateSlice();
        this._updateGeneOptions();
        this._updateIncludedAlleles();
    }

    close() {
        this.modal.close(this.included_allele_ids);
    }

    onClose() {
        // Workaround for when calling class functions
        // losing context of this...used by X in corner.
        return this.close.bind(this);
    }

    fromId(id) {
        return this.alleles.find(a => a.id === id);
    }

    _updateFilter() {
        if (this.category === 'all') {
            this.category_excluded_alleles = this.alleles.class1.concat(this.alleles.intronic);
        }
        else if (this.category === 'class_one') {
            this.category_excluded_alleles = this.alleles.class1;
        }
        else if (this.category === 'intronic') {
            this.category_excluded_alleles = this.alleles.intronic;
        }

        this.filtered_alleles = this.category_excluded_alleles.slice(0); // Clone array

        // Filter out included alleles
        if (this.included_allele_ids.length) {
            this.filtered_alleles = this.filtered_alleles.filter(a => {
                return this.included_allele_ids.find(ia => ia === a.id) === undefined;
            });
        }

        // Filter by gene symbol
        if (this.selected_gene) {
            this.filtered_alleles = this.filtered_alleles.filter(a => {
                return a.annotation.filtered.some(t => {
                    if ('SYMBOL' in t) {
                        return t.SYMBOL === this.selected_gene;
                    };
                })
            });
        }

        // Sort by gene symbol and HGVSc
        this.filtered_alleles.sort(
            firstBy(v => v.annotation.filtered[0].SYMBOL)
            .thenBy(v => v.annotation.filtered[0].HGVSc)
        );
    }

    _updateSlice() {
        this.slice = this.filtered_alleles.slice(
            (this.page_idx-1) * this.number_per_page,
            this.page_idx * this.number_per_page
        );
    }

    _updateGeneOptions() {
        this.gene_options = [];
        // Use category_excluded_alleles to make the options relate
        // to selected category
        for (let a of this.category_excluded_alleles) {
            let symbol = a.annotation.filtered[0].SYMBOL;
            if (this.gene_options.find(g => g === symbol) === undefined) {
                this.gene_options.push(symbol);
            }
        }
        this.gene_options.sort();
    }

    _updateIncludedAlleles() {
        let all_alleles = this.alleles.class1.concat(this.alleles.intronic);
        this.included_alleles = this.included_allele_ids.map(
            aid => all_alleles.find(ma => ma.id === aid)
        );
    }
}


@Service({
    serviceName: 'AddExcludedAllelesModal'
})
@Inject('$uibModal')
export class AddExcludedAllelesModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
    */

    /**
     * Popups a dialog for adding excluded alleles
     * @param  {Object} excluded_allele_ids Object with list of alleles that are excluded {class1: [..], intronic: [..]}
     * @param  {Array} included_allele_ids List of allele ids that are included
     *                 (must be subset of excluded_allele_ids). This is directly updated based on users selection.
     * @param  {int} sample_id Sample for which to load alleles
     * @param  {string} gp_name Genepanel name for which to load alleles
     * @param  {string} gp_version Genepanel version for which to load alleles
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with same array as included_allele_ids.
     */
    show(excluded_allele_ids, included_allele_ids, sample_id, gp_name, gp_version) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/addExcludedAllelesModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                'Config',
                'Allele',
                'excluded_allele_ids',
                'included_allele_ids',
                'sample_id',
                'gp_name',
                'gp_version',
                AddExcludedAllelesController
            ],
            controllerAs: 'vm',
            resolve: {
                excluded_allele_ids: () => excluded_allele_ids,
                included_allele_ids: () => included_allele_ids,
                sample_id: () => sample_id,
                gp_name: () => gp_name,
                gp_version: () => gp_version
            },
            size: 'lg'
        });

        return modal.result;

    }

}
