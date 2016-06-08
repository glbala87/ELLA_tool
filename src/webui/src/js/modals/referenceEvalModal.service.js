/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class ReferenceEvalModalController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(modalInstance,
                Config,
                Analysis,
                analysis,
                allele,
                reference,
                referenceAssessment) {
        this.config = Config.getConfig(),
        this.analysisService = Analysis;
        this.analysis = analysis;
        this.modal = modalInstance;
        this.allele = allele;
        this.reference = reference;
        this.referenceAssessment = JSON.parse(JSON.stringify(referenceAssessment));
        this.enabled_sources = [];
        this.sources = {
                'relevance': {
                    title: 'Relevance',
                    desc: 'Is reference relevant?',
                    buttons: [
                        'Yes',
                        'Indirectly',
                        'No',
                        'Ignore'
                    ],
                    buttons_store: 'relevance'
                },
                'review': {
                    title: 'Review',
                    desc: '',
                    optional: true
                },
                'aa_overlap': {
                    title: 'Overlapping amino acid',
                    desc: 'Effect of amino acid change?',
                    buttons: [
                        ['Pathogenic', 'overlap_pat'],
                        ['VUS', 'overlap_vus'],
                        ['Benign', 'overlap_ben'],
                    ],
                    buttons_store: 'ref_aa_overlap',
                    dropdown: [
                        ['Quality: Strong', 'overlap_HQ'],
                        ['Quality: Moderate', 'overlap_MQ'],
                        ['Quality: Weak', 'overlap_WQ'],
                        ['Quality: Unknown', 'overlap_UQ']
                    ],
                    dropdown_store: 'ref_aa_overlap_quality',
                    optional: true,
                    hide_when_source: 'review'
                },
                'aa_overlap_same_novel': {
                    title: '',
                    desc: 'Changes to same or novel amino acid?',
                    buttons: [
                        ['Same aa', 'same_aa'],
                        ['Novel aa', 'novel_aa'],
                    ],
                    buttons_store: 'ref_aa_overlap_same_novel',
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review'
                },
                'aa_overlap_sim': {
                    title: '',
                    desc: 'Similar amino acid properties?',
                    buttons: [
                        ['= property', 'sim_prop'],
                        ['≠ property', 'diff_prop']
                    ],
                    buttons_store: 'ref_aa_overlap_sim',
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review',
                    show_when_selection: ['ref_aa_overlap_same_novel', 'novel_aa']
                },
                'domain_overlap': {
                    title: 'Critical domain',
                    desc: 'Does the domain have known benign variation?',
                    buttons: [
                        ['Yes', 'crit_domain_ben'],
                        ['No', 'crit_domain'],
                        ['Unknown', 'crit_domain_unknown'],
                    ],
                    buttons_store: 'ref_domain_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'crit_site': {
                    title: '',
                    desc: 'In amino acid with a critical function?',
                    buttons: [
                        ['Yes', 'crit_site'],
                        ['No', 'crit_site_no'],
                        ['Unknown', 'crit_site_unknown'],
                    ],
                    buttons_store: 'crit_site',
                    optional_dep: 'domain_overlap',
                    hide_when_source: 'review'
                },
                'domain_overlap': {
                    title: 'Overlapping critical domain',
                    desc: 'Does the domain have known benign variation?',
                    buttons: [
                        ['Yes', 'crit_domain_ben'],
                        ['No', 'crit_domain'],
                        ['Unknown', 'crit_domain_unknown'],
                    ],
                    buttons_store: 'ref_domain_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'repeat_overlap': {
                    title: 'Overlapping repeat region',
                    desc: 'Does the repeat have any known function?',
                    buttons: [
                        ['Yes', 'repeat_funct'],
                        ['No', 'repeat'],
                        ['Unknown', 'repeat_unknown'],
                    ],
                    buttons_store: 'ref_repeat_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'mutational_hotspot': {
                    title: 'Mutational hot spot',
                    desc: '',
                    buttons: [
                        ['Yes', 'mut_hotspot'],
                        ['Unknown', 'mut_hotspot_unknown'],
                    ],
                    buttons_store: 'ref_mut_hotspot',
                    optional: true,
                    hide_when_source: 'review'
                },
                'other': {
                    title: 'Other',
                    desc: 'Specify below',
                    optional: true
                },
                'auth_classification': {
                    title: 'Conclusion',
                    desc: 'Author variant classification',
                    buttons: [
                        ['Pathogenic', 'pathogenic'],
                        ['VUS', 'vus'],
                        ['Neutral', 'neutral']
                    ],
                    buttons_store: 'ref_auth_classification'
                },
                'segregation': {
                    title: 'Segregation',
                    desc: 'Variant segregates with disease?',
                    buttons: [
                        ['Yes', 'segr'],
                        ['No', 'no_segr']
                    ],
                    buttons_store: 'ref_segregation',
                    dropdown: [
                        ['Quality: Strong', 'segr_HQ'],
                        ['Quality: Moderate', 'segr_MQ'],
                        ['Quality: Weak', 'segr_WQ'],
                        ['Quality: Unknown', 'segr_UQ']
                    ],
                    dropdown_store: 'ref_segregation_quality',
                    optional: true
                },
                'protein': {
                    title: 'Protein',
                    desc: 'Abnormal protein function?',
                    buttons: [
                        ['Yes', 'prot_abnormal'],
                        ['No', 'prot_normal']
                    ],
                    buttons_store: 'ref_prot',
                    dropdown: [
                        ['Quality: Strong', 'prot_HQ'],
                        ['Quality: Moderate', 'prot_MQ'],
                        ['Quality: Weak', 'prot_WQ'],
                        ['Quality: Unknown', 'prot_UQ']
                    ],
                    dropdown_store: 'ref_prot_quality',
                    optional: true
                },
                'rna': {
                    title: 'RNA',
                    desc: 'Abnormal splicing/protein expression?',
                    buttons: [
                        ['Yes', 'rna_abnormal'],
                        ['No', 'rna_normal']
                    ],
                    buttons_store: 'ref_rna',
                    dropdown: [
                        ['Quality: Strong', 'rna_HQ'],
                        ['Quality: Moderate', 'rna_MQ'],
                        ['Quality: Weak', 'rna_WQ'],
                        ['Quality: Unknown', 'rna_UQ']
                    ],
                    dropdown_store: 'ref_rna_quality',
                    optional: true
                },
                'msi': {
                    title: 'MSI',
                    desc: 'Instability demonstrated?',
                    buttons: [
                        ['Yes', 'msi'],
                        ['No', 'no_msi']
                    ],
                    buttons_store: 'ref_msi',
                    dropdown: [
                        ['Quality: Strong', 'msi_HQ'],
                        ['Quality: Moderate', 'msi_MQ'],
                        ['Quality: Weak', 'msi_WQ'],
                        ['Quality: Unknown', 'msi_UQ']
                    ],
                    dropdown_store: 'ref_msi_quality',
                    optional: true,
                    gene_group_only: 'MMR'
                },
                'ihc': {
                    title: 'IHC',
                    desc: 'Instability demonstrated?',
                    buttons: [
                        ['Yes', 'mmr_loss'],
                        ['No', 'mmr_noloss']
                    ],
                    buttons_store: 'ref_ihc',
                    dropdown: [
                        ['Quality: Strong', 'ihc_HQ'],
                        ['Quality: Moderate', 'ihc_MQ'],
                        ['Quality: Weak', 'ihc_WQ'],
                        ['Quality: Unknown', 'ihc_UQ']
                    ],
                    dropdown_store: 'ref_ihc_quality',
                    dropdown_when_selection: ['ref_ihc', 'mmr_loss'],
                    optional: true,
                    gene_group_only: 'MMR'
                },
                'prediction': {
                    title: 'In silico',
                    desc: 'Results of prediction tools?',
                    buttons: [
                        ['Pathogenic', 'pat'],
                        ['Neutral', 'neu'],
                    ],
                    buttons_store: 'ref_prediction',
                    textfield: "Enter tool...",
                    textfield_store: "ref_prediction_tool",
                    optional: true
                },
                'population': {
                    title: 'Population',
                    desc: 'Observed in unrelated affecteds or present in healthy?',
                    buttons: [
                        ['>=4 affected', 'in_many_aff'],
                        ['3 affected', 'in_more_ff'],
                        ['2 affected', 'in_few_affected'],
                        ['Healthy', 'in_healthy'],
                    ],
                    buttons_store: 'ref_population',
                    optional: true
                },
                'quality': {
                    title: 'Overall quality',
                    desc: '',
                    buttons: [
                        ['Excellent', 'excellent'],
                        ['Good', 'good'],
                        ['Passable', 'passable'],
                        ['Lacking', 'lacking'],
                        ['Poor', 'poor'],
                    ],
                    buttons_store: 'ref_quality'
                }
            };

            this.relevance_show = {
                'Yes': [
                    'auth_classification',
                    'segregation',
                    'protein',
                    'rna',
                    'msi',
                    'ihc',
                    'prediction',
                    'population',
                    'quality'
                ],
                'Indirectly': [
                    'review',
                    'aa_overlap',
                    'aa_overlap_same_novel',
                    'aa_overlap_sim',
                    'domain_overlap',
                    'crit_site',
                    'mutational_hotspot',
                    'repeat_overlap',
                    'other',
                    'quality'
                ],
                'No': [],
                'Ignore': []
            };

        this._setup();
    }

    _setup() {
        if (!this.referenceAssessment.evaluation) {
            this.referenceAssessment.evaluation = {};
            this.referenceAssessment.evaluation.sources = [];
            this.referenceAssessment.evaluation.relevance = 'Yes';
        }
    }

    _alleleInGeneGroup(group) {
        let genes = this.allele.annotation.filtered.map(a => a.SYMBOL);
        return this.config.classification.gene_groups[group].some(g => genes.includes(g));
    }

    /**
     * Returns the sources to list as options
     */
    getSources() {
        return this.relevance_show[this.referenceAssessment.evaluation.relevance];
    }

    /**
     * Return whether this source should be displayed
     * @param  {String} source Name of source
     * @return {bool}  Whether the source should be shown
     */
    shouldShow(source) {
        let should_show = true;

        if ('gene_group_only' in this.sources[source]) {
            return this._alleleInGeneGroup(this.sources[source].gene_group_only);
        }

        if ('hide_when_source' in this.sources[source]) {
            should_show = !this.referenceAssessment.evaluation.sources.includes(
                this.sources[source].hide_when_source
            );
        }

        if ('show_when_selection' in this.sources[source]) {
            if (!should_show) {
                return false;
            }
            return this.referenceAssessment.evaluation[this.sources[source].show_when_selection[0]] === this.sources[source].show_when_selection[1];
        }
        else {
            return should_show;
        }
    }

    /**
     * Returns whether this source should be disabled,
     * by checking this.enabled for the source name,
     * or if the optional_dep is set, whether the dependancy
     * name is enabled.
     */
    isDisabled(source) {
        let optional = false;
        if ('optional' in this.sources[source]) {
            optional = this.sources[source].optional;
            if (!optional) {
                return false;
            }
        }

        if ('optional_dep' in this.sources[source]) {
            source = this.sources[source].optional_dep;
            optional = true;
        }
        if (optional) {
            return this.referenceAssessment.evaluation.sources.find(e => e === source) === undefined;
        }
        else {
            return false;
        }
    }

    /**
     * Cleans up the evaluation, removing all data that is not
     * selected or not shown in the UI.
     * Reason is to not store any user selection that is no more
     * relevant.
     */
    cleanup() {

        for (let [source, source_data] of Object.entries(this.sources)) {
            // relevance is special
            if (source === 'relevance') {
                continue;
            }
            // If not visible or disabled -> delete data
            if (!this.getSources().includes(source) ||
                this.isDisabled(source) ||
                (this.getSources().includes(source) && !this.shouldShow(source))) {
                // Clean up evaluation
                if ('buttons_store' in source_data) {
                    delete this.referenceAssessment.evaluation[source_data.buttons_store];
                }
                if ('dropdown_store' in source_data) {
                    delete this.referenceAssessment.evaluation[source_data.dropdown_store];
                }
                if ('textfield_store' in source_data) {
                    delete this.referenceAssessment.evaluation[source_data.textfield_store];
                }
                // Clean up enabled sources
                let idx = this.referenceAssessment.evaluation.sources.findIndex(e => e === source);
                if (idx >= 0) {
                    this.referenceAssessment.evaluation.sources.splice(idx, 1);
                }
            }

        }

    }

    save() {
        this.cleanup();
        return this.modal.close(this.referenceAssessment);
    }

}

@Service({
    serviceName: 'ReferenceEvalModal'
})
@Inject('$uibModal')
export class ReferenceEvalModal {

    constructor($uibModal) {
        this.modalService = $uibModal;
    }

    /**
     * Popups a dialog for doing reference evaluation
     * @param  {Allele} Allele for reference evaluation
     * @param  {Reference} Reference to be evaluated
     * @param  {Object} Data for reference assessment
     * @return {Promise} Promise that resolves when dialog is closed.
     */
    show(analysis, allele, reference, referenceAssessment) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/referenceEvalModal.ngtmpl.html',
            controller: ['$uibModalInstance', 'Config', 'Analysis', 'analysis', 'allele', 'reference', 'referenceAssessment', ReferenceEvalModalController],
            controllerAs: 'vm',
            resolve: {
                analysis: analysis,
                allele: () => allele,
                reference: () => reference,
                referenceAssessment: () => referenceAssessment,
            },
            size: 'lg'
        });

        return modal.result;

    }

}
