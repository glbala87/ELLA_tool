import isReadOnly from '../computed/isReadOnly'

export class AddExcludedAllelesController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(
        modalInstance,
        Allele,
        excluded_allele_ids,
        included_allele_ids,
        config,
        sample_id,
        gp_name,
        gp_version,
        read_only
    ) {
        this.modal = modalInstance
        this.frequencies = config.frequencies
        this.alleleService = Allele
        this.included_allele_ids = included_allele_ids // Alleles added by user
        this.alleles = [] // Alleles loaded from backend
        this.excluded_allele_ids = excluded_allele_ids
        this.category_excluded_alleles = [] // Alleles filtered on the category, but no further filtering. Needed for showing genes
        this.filtered_alleles = [] // Finished filtered Alleles to show, that are not yet added
        this.included_alleles = [] // Alleles added by user (internal use)
        this.category = 'all'
        this.slice = [] // Holds the slice of alleles for pagination
        this.gene_options = [] // Options for gene selection dropdown
        this.selected_gene = null
        this.page_idx = 1
        this.number_per_page = 3
        this.readOnly = read_only

        this.loadAlleles(sample_id, gp_name, gp_version)
    }

    /**
     * Load in all allele data from backend (yes, all x hundreds at once, we're lazy...)
     * TODO: Improve performance with pagination if necessary
     */
    loadAlleles(sample_id, gp_name, gp_version) {
        let all_ids = this._getAllExcludedAlleleIds()

        this.alleleService
            .getAlleles(all_ids, sample_id, gp_name, gp_version)
            .then((alleles) => (this.alleles = alleles))
            .then(() => this.update())
    }

    _getAllExcludedAlleleIds() {
        let all_ids = []
        for (let ids of Object.values(this.excluded_allele_ids)) {
            all_ids.push(...ids)
        }
        return all_ids
    }

    update() {
        this._updateFilter()
        this._updateSlice()
        this._updateGeneOptions()
        this._updateIncludedAlleles()
    }

    close() {
        if (this.readOnly) {
            this.modal.close() // close without reporting state
            return
        }

        this.modal.close(this.included_allele_ids)
    }

    onClose() {
        // Workaround for when calling class functions
        // losing context of this...used by X in corner.
        return this.close.bind(this)
    }

    fromId(id) {
        return this.alleles.find((a) => a.id === id)
    }

    _updateFilter() {
        if (this.category === 'all') {
            this.category_excluded_alleles = this.alleles.slice(0)
        } else if (this.category === 'frequency') {
            this.category_excluded_alleles = this.alleles.filter((a) =>
                this.excluded_allele_ids.frequency.includes(a.id)
            )
        } else if (this.category === 'gene') {
            this.category_excluded_alleles = this.alleles.filter((a) =>
                this.excluded_allele_ids.gene.includes(a.id)
            )
        } else if (this.category === 'intronic') {
            this.category_excluded_alleles = this.alleles.filter((a) =>
                this.excluded_allele_ids.intronic.includes(a.id)
            )
        }

        this.filtered_alleles = this.category_excluded_alleles.slice(0) // Clone array

        // Filter out included alleles
        if (this.included_allele_ids.length) {
            this.filtered_alleles = this.filtered_alleles.filter((a) => {
                return this.included_allele_ids.find((ia) => ia === a.id) === undefined
            })
        }

        // Filter by gene symbol
        if (this.selected_gene) {
            this.filtered_alleles = this.filtered_alleles.filter((a) => {
                return a.annotation.filtered.some((t) => {
                    if ('symbol' in t) {
                        return t.symbol === this.selected_gene
                    }
                })
            })
        }

        // Sort by gene symbol and HGVSc
        this.filtered_alleles.sort(
            firstBy((v) => v.annotation.filtered[0].symbol).thenBy(
                (v) => v.annotation.filtered[0].HGVSc
            )
        )
    }

    _updateSlice() {
        this.slice = this.filtered_alleles.slice(
            (this.page_idx - 1) * this.number_per_page,
            this.page_idx * this.number_per_page
        )
    }

    _updateGeneOptions() {
        this.gene_options = []
        // Use category_excluded_alleles to make the options relate
        // to selected category
        for (let a of this.category_excluded_alleles) {
            let symbol = a.annotation.filtered[0].symbol
            if (this.gene_options.find((g) => g === symbol) === undefined) {
                this.gene_options.push(symbol)
            }
        }
        this.gene_options.sort()
    }

    _updateIncludedAlleles() {
        this.included_alleles = this.alleles.filter((a) => this.included_allele_ids.includes(a.id))
    }
}

// TODO: $uibModal is only temporary until we get rid of angular modals
export default function showAddExcludedModal({ state, $uibModal, resolve }) {
    const analysis = state.get('views.workflows.data.analysis')
    const interpretation = state.get('views.workflows.interpretation.selected')
    const genepanel = state.get('views.workflows.data.genepanel')
    const config = state.get('app.config')
    const readOnly = resolve.value(isReadOnly)

    const manuallyAddedAlleles = [...interpretation.state.manuallyAddedAlleles]

    let modal = $uibModal.open({
        templateUrl: 'ngtmpl/addExcludedAllelesModal.ngtmpl.html',
        controller: [
            '$uibModalInstance',
            'Allele',
            'excluded_allele_ids',
            'included_allele_ids',
            'config',
            'sample_id',
            'gp_name',
            'gp_version',
            'read_only',
            AddExcludedAllelesController
        ],
        controllerAs: 'vm',
        resolve: {
            excluded_allele_ids: () => interpretation.excluded_allele_ids,
            included_allele_ids: () => manuallyAddedAlleles,
            config: () => config,
            sample_id: () => analysis.samples[0].id, // FIXME: Support multiple samples
            gp_name: () => genepanel.name,
            gp_version: () => genepanel.version,
            read_only: () => readOnly
        },
        size: 'lg'
    })

    return modal.result
        .then(() => {
            return { manuallyAddedAlleles }
        })
        .catch(() => {
            return { manuallyAddedAlleles }
        })
}
