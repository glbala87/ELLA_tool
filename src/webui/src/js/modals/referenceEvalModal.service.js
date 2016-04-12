/* jshint esnext: true */
import {Service, Inject} from '../ng-decorators';

export class ReferenceEvalModalController {
    /**
     * Controller for dialog asking user to add filtered alleles.
     */

    constructor(modalInstance,
                Analysis,
                analysis,
                allele,
                reference,
                referenceAssessment) {
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
                    options: [
                        'Yes',
                        'Indirectly',
                        'No',
                        'Ignore'
                    ],
                    store: 'relevance'
                },
                'review': {
                    title: 'Review',
                    desc: '',
                    optional: true
                },
                'aa_overlap': {
                    title: 'Overlapping amino acid',
                    desc: 'Effect of amino acid change?',
                    options: [
                        ['Pathogenic', 'overlap_pat'],
                        ['Benign', 'overlap_ben'],
                    ],
                    store: 'ref_aa_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'aa_overlap_same_novel': {
                    title: '',
                    desc: 'Changes to same or novel amino acid?',
                    options: [
                        ['Same aa', 'same_aa'],
                        ['Novel aa', 'novel_aa'],
                    ],
                    store: 'ref_aa_overlap_same_novel',
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review'
                },
                'aa_overlap_sim': {
                    title: '',
                    desc: 'Similar amino acid properties?',
                    options: [
                        ['= property', 'sim_prop'],
                        ['≠ property', 'diff_prop']
                    ],
                    store: 'ref_aa_overlap_sim',
                    optional_dep: 'aa_overlap',
                    hide_when_source: 'review',
                    show_when_selection: ['ref_aa_overlap_same_novel', 'novel_aa']
                },
                'domain_overlap': {
                    title: 'Overlapping critical domain',
                    desc: 'Does the domain have known benign variation?',
                    options: [
                        ['Yes', 'crit_domain_ben'],
                        ['No', 'crit_domain'],
                        ['Unknown', 'crit_domain_unknown'],
                    ],
                    store: 'ref_domain_overlap',
                    optional: true,
                    hide_when_source: 'review'
                },
                'repeat_overlap': {
                    title: 'Overlapping repeat region',
                    desc: 'Does the repeat have any known function?',
                    options: [
                        ['Yes', 'repeat_funct'],
                        ['No', 'repeat'],
                        ['Unknown', 'repeat_unknown'],
                    ],
                    store: 'ref_repeat_overlap',
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
                    options: [
                        ['Pathogenic', 'pathogenic'],
                        ['VUS', 'vus'],
                        ['Neutral', 'neutral']
                    ],
                    store: 'ref_auth_classification'
                },
                'segregation': {
                    title: 'Segregation',
                    desc: 'Variant segregates with disease?',
                    options: [
                        ['Strong', 'segr+++'],
                        ['Moderate', 'segr++'],
                        ['Weak', 'segr+'],
                        ['No', 'segr-'],
                    ],
                    store: 'ref_segregation',
                    optional: true
                },
                'protein': {
                    title: 'Protein',
                    desc: 'Abnormal protein function?',
                    options: [
                        ['++', 'prot++'],
                        ['+', 'prot+'],
                        ['-', 'prot-'],
                        ['--', 'prot--'],
                    ],
                    store: 'ref_prot',
                    optional: true
                },
                'rna': {
                    title: 'RNA',
                    desc: 'Abnormal splicing/protein expression?',
                    options: [
                        ['++', 'rna++'],
                        ['+', 'rna+'],
                        ['-', 'rna-'],
                        ['--', 'rna--'],
                    ],
                    store: 'ref_rna',
                    optional: true
                },
                'prediction': {
                    title: 'In silico',
                    desc: 'Results of prediction tools?',
                    options: [
                        ['Pathogenic', 'pat'],
                        ['Neutral', 'neu'],
                    ],
                    store: 'ref_prediction',
                    optional: true
                },
                'population': {
                    title: 'Population',
                    desc: 'Increased in affecteds or present in documented healthy?',
                    options: [
                        ['RR>5', 'rr5'],
                        ['Affecteds', 'in_affecteds'],
                        ['Healthy', 'in_healthy'],
                    ],
                    store: 'ref_population',
                    optional: true
                },
                'quality': {
                    title: 'Overall quality',
                    desc: '',
                    options: [
                        ['Excellent', 'excellent'],
                        ['Good', 'good'],
                        ['Passable', 'passable'],
                        ['Lacking', 'lacking'],
                        ['Poor', 'poor'],
                    ],
                    store: 'ref_quality'
                }
            };

            this.relevance_show = {
                'Yes': [
                    'auth_classification',
                    'segregation',
                    'protein',
                    'rna',
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
                delete this.referenceAssessment.evaluation[source_data.store];
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
            controller: ['$uibModalInstance', 'Analysis', 'analysis', 'allele', 'reference', 'referenceAssessment', ReferenceEvalModalController],
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
