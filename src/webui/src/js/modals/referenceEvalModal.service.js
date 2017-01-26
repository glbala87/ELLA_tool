/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';
import {deepCopy, deepEquals} from '../util';


export class ReferenceEvalModalController {
    /**
     * Controller for dialog with reference evaluation.
     */

    constructor(modalInstance,
                Config,
                Analysis,
                analysis,
                allele,
                reference,
                referenceAssessment,
                readOnly) {
        this.config = Config.getConfig();
        this.analysisService = Analysis;
        this.analysis = analysis;
        this.modal = modalInstance;
        this.allele = allele;
        this.reference = reference;
        this.existingReferenceAssessment = referenceAssessment;
        this.referenceAssessment = deepCopy(referenceAssessment);
        this.readOnly = readOnly;
        this.enabled_sources = [];
        this.sources = {
                // 'relevance' is a special case, so it has no 'elements' block like the others
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
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Pathogenic', 'overlap_pat'],
                                ['VUS', 'overlap_vus'],
                                ['Benign', 'overlap_ben'],
                            ],
                            store: 'ref_aa_overlap'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'overlap_HQ'],
                                ['Quality: Moderate', 'overlap_MQ'],
                                ['Quality: Weak', 'overlap_WQ'],
                                ['Quality: Unknown', 'overlap_UQ']
                            ],
                            store: 'ref_aa_overlap_quality'
                        }
                    ],
                    optional: true,
                    hide_when_source: 'review'
                },
                'aa_overlap_same_novel': {
                    title: '',
                    desc: 'Changes to same or novel amino acid?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Same aa', 'same_aa'],
                                ['Novel aa', 'novel_aa'],
                            ],
                            store: 'ref_aa_overlap_same_novel'
                        }
                    ],
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review'
                },
                'aa_overlap_sim': {
                    title: '',
                    desc: 'Similar amino acid properties?',
                    elements: [
                        {
                            type: 'dropdown',
                            options: [
                                ['Ala', 'Ala'],
                                ['Cys', 'Cys'],
                                ['Asp', 'Asp'],
                                ['Glu', 'Glu'],
                                ['Phe', 'Phe'],
                                ['Gly', 'Gly'],
                                ['His', 'His'],
                                ['Ile', 'Ile'],
                                ['Lys', 'Lys'],
                                ['Leu', 'Leu'],
                                ['Met', 'Met'],
                                ['Asn', 'Asn'],
                                ['Pro', 'Pro'],
                                ['Gln', 'Gln'],
                                ['Arg', 'Arg'],
                                ['Ser', 'Ser'],
                                ['Thr', 'Thr'],
                                ['Val', 'Val'],
                                ['Trp', 'Trp'],
                                ['Tyr', 'Tyr'],
                                ['*', '*']
                            ],
                            store: 'ref_aa_overlap_aa'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Ala', 'Ala'],
                                ['Cys', 'Cys'],
                                ['Asp', 'Asp'],
                                ['Glu', 'Glu'],
                                ['Phe', 'Phe'],
                                ['Gly', 'Gly'],
                                ['His', 'His'],
                                ['Ile', 'Ile'],
                                ['Lys', 'Lys'],
                                ['Leu', 'Leu'],
                                ['Met', 'Met'],
                                ['Asn', 'Asn'],
                                ['Pro', 'Pro'],
                                ['Gln', 'Gln'],
                                ['Arg', 'Arg'],
                                ['Ser', 'Ser'],
                                ['Thr', 'Thr'],
                                ['Val', 'Val'],
                                ['Trp', 'Trp'],
                                ['Tyr', 'Tyr'],
                                ['*', '*']
                            ],
                            store: 'ref_aa_overlap_aa_ref'
                        },
                        {
                            type: 'button',
                            options: [
                                ['= property', 'sim_prop'],
                                ['≠ property', 'diff_prop']
                            ],
                            store: 'ref_aa_overlap_sim'
                        }
                    ],
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review',
                    show_when_selection: ['ref_aa_overlap_same_novel', 'novel_aa']
                },
                'domain_overlap': {
                    title: 'Critical domain',
                    desc: 'Does the domain have known benign variation?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'crit_domain_ben'],
                                ['No', 'crit_domain'],
                                ['Unknown', 'crit_domain_unknown'],
                            ],
                            store: 'ref_domain_overlap'
                        }
                    ],
                    buttons_store: 'ref_domain_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'crit_site': {
                    title: '',
                    desc: 'In amino acid with a critical function?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'crit_site'],
                                ['No', 'crit_site_no'],
                                ['Unknown', 'crit_site_unknown'],
                            ],
                            store: 'ref_crit_site'
                        }
                    ],
                    optional_dep: 'domain_overlap',
                    hide_when_source: 'review'
                },
                'domain_overlap': {
                    title: 'Overlapping critical domain',
                    desc: 'Does the domain have known benign variation?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'crit_domain_ben'],
                                ['No', 'crit_domain'],
                                ['Unknown', 'crit_domain_unknown'],
                            ],
                            store: 'ref_domain_overlap'
                        }
                    ],
                    optional: true,
                    hide_when_source: 'review'
                },
                'repeat_overlap': {
                    title: 'Overlapping repeat region',
                    desc: 'Does the repeat have any known function?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'repeat_funct'],
                                ['No', 'repeat'],
                                ['Unknown', 'repeat_unknown'],
                            ],
                            store: 'ref_repeat_overlap'
                        }
                    ],
                    buttons_store: 'ref_repeat_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'mutational_hotspot': {
                    title: 'Mutational hot spot',
                    desc: '',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'mut_hotspot'],
                                ['Unknown', 'mut_hotspot_unknown'],
                            ],
                            store: 'ref_mut_hotspot'
                        }
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
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Pathogenic', 'pathogenic'],
                                ['VUS', 'vus'],
                                ['Neutral', 'neutral']
                            ],
                            store: 'ref_auth_classification'
                        }
                    ]
                },
                'segregation': {
                    title: 'Segregation',
                    desc: 'Variant segregates with disease?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'segr'],
                                ['No', 'no_segr']
                            ],
                            store: 'ref_segregation'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'segr_HQ'],
                                ['Quality: Moderate', 'segr_MQ'],
                                ['Quality: Weak', 'segr_WQ'],
                                ['Quality: Unknown', 'segr_UQ']
                            ],
                            store: 'ref_segregation_quality'
                        }
                    ],
                    optional: true
                },
                'protein': {
                    title: 'Protein',
                    desc: 'Abnormal protein function?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'prot_abnormal'],
                                ['No', 'prot_normal']
                            ],
                            store: 'ref_prot'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'prot_HQ'],
                                ['Quality: Moderate', 'prot_MQ'],
                                ['Quality: Weak', 'prot_WQ'],
                                ['Quality: Unknown', 'prot_UQ']
                            ],
                            store: 'ref_prot_quality'
                        }
                    ],
                    optional: true
                },
                'rna': {
                    title: 'RNA',
                    desc: 'Abnormal splicing/protein expression?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'rna_abnormal'],
                                ['No', 'rna_normal']
                            ],
                            store: 'ref_rna'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'rna_HQ'],
                                ['Quality: Moderate', 'rna_MQ'],
                                ['Quality: Weak', 'rna_WQ'],
                                ['Quality: Unknown', 'rna_UQ']
                            ],
                            store: 'ref_rna_quality'
                        }
                    ],
                    optional: true
                },
                'msi': {
                    title: 'MSI',
                    desc: 'Instability demonstrated?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'msi'],
                                ['No', 'no_msi']
                            ],
                            store: 'ref_msi'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'msi_HQ'],
                                ['Quality: Moderate', 'msi_MQ'],
                                ['Quality: Weak', 'msi_WQ'],
                                ['Quality: Unknown', 'msi_UQ']
                            ],
                            store: 'ref_msi_quality'
                        }
                    ],
                    optional: true,
                    gene_group_only: 'MMR'
                },
                'ihc': {
                    title: 'IHC',
                    desc: 'Instability demonstrated?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Yes', 'mmr_loss'],
                                ['No', 'mmr_noloss']
                            ],
                            store: 'ref_ihc'
                        },
                        {
                            type: 'dropdown',
                            options: [
                                ['Quality: Strong', 'ihc_HQ'],
                                ['Quality: Moderate', 'ihc_MQ'],
                                ['Quality: Weak', 'ihc_WQ'],
                                ['Quality: Unknown', 'ihc_UQ']
                            ],
                            store: 'ref_ihc_quality',
                            when_selection: ['ref_ihc', 'mmr_loss']
                        }
                    ],
                    optional: true,
                    gene_group_only: 'MMR'
                },
                'prediction': {
                    title: 'In silico',
                    desc: 'Results of prediction tools?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Pathogenic', 'pat'],
                                ['VUS', 'vus'],
                                ['Neutral', 'neu'],
                            ],
                            store: 'ref_prediction'
                        },
                        {
                            type: 'text',
                            placeholder: 'Enter tool...',
                            store: 'ref_prediction_tool'
                        }
                    ],
                    optional: true
                },
                'population': {
                    title: 'Population',
                    desc: 'Observed in UNRELATED affecteds or present in healthy?',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['>=4 affected', 'in_many_aff'],
                                ['3 affected', 'in_more_ff'],
                                ['1-2 affected', 'in_few_affected'],
                                ['Healthy', 'in_healthy'],
                            ],
                            store: 'ref_population'
                        }
                    ],
                    optional: true
                },
                'quality': {
                    title: 'Overall quality',
                    desc: '',
                    elements: [
                        {
                            type: 'button',
                            options: [
                                ['Excellent', 'excellent'],
                                ['Good', 'good'],
                                ['Passable', 'passable'],
                                ['Lacking', 'lacking'],
                                ['Poor', 'poor'],
                            ],
                            store: 'ref_quality'
                        }
                    ]
                }
            };

            this.relevance_show = {
                'Yes': [
                    'auth_classification',
                    'segregation',
                    'population',
                    'protein',
                    'rna',
                    'msi',
                    'ihc',
                    'prediction',
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
        }
        if (!this.referenceAssessment.evaluation.sources) {
            this.referenceAssessment.evaluation.sources = [];
        }
        if (!this.referenceAssessment.evaluation.relevance) {
            this.referenceAssessment.evaluation.relevance = 'Yes';
        }
    }

    _isAlleleInGeneGroup(group) {
        let genes = this.allele.annotation.filtered.map(a => a.symbol);
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
            return this._isAlleleInGeneGroup(this.sources[source].gene_group_only);
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

    isDropdownDisabled(source) {

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
                if ('elements' in source_data) {
                    for (let elem of source_data.elements) {
                        delete this.referenceAssessment.evaluation[elem.store];
                    }
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
        if (!deepEquals(this.existingReferenceAssessment, this.referenceAssessment)) {
            return this.modal.close(this.referenceAssessment);
        }
        else {
            return this.modal.close();
        }
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
     * Popups a dialog for doing reference evaluation.
     *
     * The returned promise will resolve with the changed data,
     * if anything has changed, otherwise it resolves with undefined.
     *
     * @param  {Allele} Allele for reference evaluation
     * @param  {Reference} Reference to be evaluated
     * @param  {Object} Data for reference assessment
     * @param  {boolean} don't save changes if read-only
     * @return {Promise} Promise that resolves when dialog is closed.
     */
    show(analysis, allele, reference, referenceAssessment, readOnly) {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/referenceEvalModal.ngtmpl.html',
            controller: ['$uibModalInstance', 'Config', 'Analysis', 'analysis', 'allele', 'reference', 'referenceAssessment', 'readOnly', ReferenceEvalModalController],
            controllerAs: 'vm',
            resolve: {
                analysis: analysis,
                allele: () => allele,
                reference: () => reference,
                referenceAssessment: () => referenceAssessment,
                readOnly: () => readOnly,
            },
            size: 'lg',
            backdrop: 'static', // Disallow closing by clicking outside
        });

        return modal.result;

    }

}
