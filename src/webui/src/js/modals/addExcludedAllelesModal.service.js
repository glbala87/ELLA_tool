/* jshint esnext: true */

(function () {
    angular.module('workbench')
        .factory('AddExcludedAllelesModal', ['$modal', function ($modal) {
            return new AddExcludedAllelesModal($modal);
        }]);

    /**
     * Controller for dialog asking user to add filtered alleles.
     */
    class AddExcludedAllelesController {

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
            this.excluded_alleles = [];  // Alleles to show, that are not yet added
            this.included_allele_ids = included_allele_ids;  // Alleles added by user
            this.filter_type = 'all';
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
            if (this.filter_type === 'all') {
                this.excluded_alleles = this.master_alleles.slice(0); // Copy array
            }
            else if (this.filter_type === 'class_one') {
                this.excluded_alleles = this.alleleFilter.invert(
                    this.alleleFilter.filterClass1(this.master_alleles),
                    this.master_alleles
                );
            }
            else if (this.filter_type === 'intronic') {
                this.excluded_alleles = this.alleleFilter.invert(
                    this.alleleFilter.filterIntronicAlleles(this.master_alleles),
                    this.master_alleles
                );
            }

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
            for (let a of this.master_alleles) {
                let symbol = a.annotation.filtered[0].SYMBOL;
                if (this.gene_options.find(g => g === symbol) === undefined) {
                    this.gene_options.push(symbol);
                }
            }
            this.gene_options.sort();
        }
    }


    class AddExcludedAllelesModal {

        constructor($modal) {
            this.modalService = $modal;
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
                controller: ['$modalInstance', '$timeout', 'Config', 'AlleleFilter', 'excluded_alleles', 'included_allele_ids', AddExcludedAllelesController],
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

})();
