/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class AddExcludedAllelesController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(modalInstance,
                $timeout,
                Config,
                AlleleFilter,
                excluded_alleles,
                included_allele_ids) {
        this.modal = modalInstance;
        this.timeout = $timeout;
        this.frequencies = Config.getConfig().frequencies;
        this.alleleFilter = AlleleFilter;
        this.master_alleles = excluded_alleles;
        this.category_excluded_alleles = []; // Alleles filtered on the category, but no further filtering
        this.excluded_alleles = [];  // Finished filtered Alleles to show, that are not yet added
        this.included_allele_ids = included_allele_ids;  // Alleles added by user
        this.category = 'all';
        this.slice = []; // Holds the slice of alleles for pagination
        this.gene_options = []; // Options for gene selection dropdown
        this.selected_gene = null;
        this.page_idx = 1;
        this.number_per_page = 5;
        this.update();
    }

    update() {
        // use timeout due to checkbox-model not updating
        // model before triggering
        this.timeout(() => {
            this._updateFilter();
            this._updateSlice();
            this._updateGeneOptions();
        });
    }

    close() {
        this.modal.close(this.included_allele_ids);
    }

    fromId(id) {
        return this.master_alleles.find(a => a.id === id);
    }

    _updateFilter() {
        if (this.category === 'all') {
            this.category_excluded_alleles = this.master_alleles.slice(0); // Copy array
        }
        else if (this.category === 'class_one') {
            this.category_excluded_alleles = this.alleleFilter.invert(
                this.alleleFilter.filterClass1(this.master_alleles),
                this.master_alleles
            );
        }
        else if (this.category === 'intronic') {
            // Only show intronic variants that are not class 1
            // hence start with non-class-1
            let non_class1 = this.alleleFilter.filterClass1(this.master_alleles);

            this.category_excluded_alleles = this.alleleFilter.invert(
                this.alleleFilter.filterIntronicAlleles(non_class1),
                non_class1
            );
        }

        // Clone array to excluded_alleles, to update the display list
        this.excluded_alleles = this.category_excluded_alleles.slice(0);

        // Filter out included alleles
        if (this.included_allele_ids.length) {
            this.excluded_alleles = this.excluded_alleles.filter(a => {
                return this.included_allele_ids.find(ia => ia === a.id) === undefined;
            });
        }

        // Filter by gene symbol
        if (this.selected_gene) {
            this.excluded_alleles = this.excluded_alleles.filter(a => {
                return a.annotation.filtered[0].SYMBOL === this.selected_gene;
            });
        }

        // Sort by gene symbol and HGVSc
        this.excluded_alleles.sort(
            firstBy(v => v.annotation.filtered[0].SYMBOL)
            .thenBy(v => v.annotation.filtered[0].HGVSc)
        );

    }

    _updateSlice() {
        this.slice = this.excluded_alleles.slice(
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
     * @param  {Array} excluded_alleles List of alleles that are excluded
     * @param  {Array} included_allele_ids List of allele ids that are included
     *                 (must be subset of excluded_alleles). This is directly updated based on users selection.
     * @return {Promise} Promise that resolves when dialog is closed. Resolves with same array as included_allele_ids.
     */
    show(excluded_alleles, included_allele_ids) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/addExcludedAllelesModal.ngtmpl.html',
            controller: ['$uibModalInstance', '$timeout', 'Config', 'AlleleFilter', 'excluded_alleles', 'included_allele_ids', AddExcludedAllelesController],
            controllerAs: 'vm',
            resolve: {
                excluded_alleles: () => excluded_alleles,
                included_allele_ids: () => included_allele_ids,
            },
            size: 'lg'
        });

        return modal.result;

    }

}
