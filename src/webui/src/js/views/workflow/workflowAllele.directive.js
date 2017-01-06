/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'workflow-allele',
    scope: {
        referenceGenome: '@',
        variantSelector: '@',
        genepanelName: '@',
        genepanelVersion: '@'
    },
    templateUrl: 'ngtmpl/workflowAllele.ngtmpl.html'
})
@Inject('$rootScope',
    '$scope',
    'WorkflowResource',
    'AlleleResource',
    'Workflow',
    'Navbar',
    'Config',
    'User')
export class WorkflowAlleleController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                AlleleResource,
                Workflow,
                Navbar,
                Config,
                User) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.alleleResource = AlleleResource;
        this.workflowService = Workflow;
        this.analysis = null;
        this.active_interpretation = null;
        this.navbar = Navbar;
        this.config = Config.getConfig();
        this.user = User;

        this.components = [ // instantiated/rendered in AlleleSectionboxContentController
            {
                title: 'Classification',
                sections: [
                    {
                        title: 'Classification',
                        options: {
                            collapsed: false
                        },
                        controls: [
                            'classification',
                            'reuse_classification'
                        ],
                        alleleassessment_comment: {
                                placeholder: 'EVALUATION',
                                name: 'classification'
                            },
                        report_comment: {
                            placeholder: 'REPORT',
                            modelname: 'evaluation'
                        },
                        content: [
                            {'tag': 'allele-info-acmg-selection'},
                            {'tag': 'allele-info-vardb'}
                        ],
                    },
                    {
                        title: 'Frequency & QC',
                        options: {
                            collapsed: false
                        },
                        controls: [
                            'copy_alamut',
                            'toggle_class1',
                            'toggle_class2',
                            'toggle_technical'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'FREQUENCY-COMMENTS',
                            name: 'frequency'
                        },
                        content: [
                            {'tag': 'allele-info-frequency-exac'},
                            {'tag': 'allele-info-frequency-thousandg'},
                            {'tag': 'allele-info-frequency-esp6500'},
                            {'tag': 'allele-info-frequency-indb'},
                            {'tag': 'allele-info-dbsnp'}
                        ],
                    },
                    {
                        title: 'External',
                        options: {
                            collapsed: false
                        },
                        controls: [
                            'custom_external'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'EXTERNAL DB-COMMENTS',
                            name: 'external'
                        },
                        content: [
                            {'tag': 'allele-info-hgmd'},
                            {'tag': 'allele-info-clinvar'},
                            {'tag': 'allele-info-external-other'}
                        ],
                    },
                    {
                        title: 'Prediction',
                        options: {
                            collapsed: false
                        },
                        controls: [
                            'custom_prediction'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'PREDICTION-COMMENTS',
                            name: 'prediction'
                        },
                        content: [
                            {'tag': 'allele-info-consequence'},
                            {'tag': 'allele-info-splice'},
                            {'tag': 'allele-info-prediction-other'},
                        ],
                    },
                    {
                        title: 'References',
                        options: {
                            collapsed: false
                        },
                        controls: [
                            'references'
                        ],
                        content: [
                            {'tag': 'allele-info-references'}
                        ],
                    }
                ]
            }
        ];

        this.selected_component = this.components[0];

        this.alleles = []; // Holds allele based on directive params. Array since "everything" expects an array...

        this.selected_interpretation = null; // Holds displayed interpretation
        this.selected_interpretation_alleles = []; // Loaded allele for current interpretation (annotation etc data can change based on interpretation snapshot)
        this.alleles_loaded = false;  // Loading indicators etc

        this.interpretations = []; // Holds interpretations from backend
        this.history_interpretations = []; // Filtered interpretations, containing only the finished ones. Used in dropdown
        this.interpretations_loaded = false; // For hiding view until we've checked whether we have interpretations

        this.dummy_interpretation = { // Dummy data for letting the user browse the view before starting interpretation. Never stored!
            genepanel_name: this.genepanelName,
            genepanel_version: this.genepanelVersion,
            state: {},
            user_state: {}
        }

        this.setUpListeners();
        this._setWatchers();

        this.loadAlleleId().then(() => {
            this.dummy_interpretation.allele_ids = [this.allele_id];
            this.reloadInterpretationData();
            this.setupNavbar();
        });
    }

    setUpListeners() {
        // Setup listener for asking user if they really want to navigate
        // away from page if unsaved changes
        let unregister_func = this.rootScope.$on('$stateChangeStart', (event) => {  // TODO: create switch to disable in CI/test
            if (this.config.app.user_confirmation_on_state_change && this.isInterpretationOngoing() && this.selected_interpretation.dirty) {
                this.confirmAbortInterpretation(event);
            }
        });

        // Unregister when scope is destroyed.
        this.scope.$on('$destroy', () => {
            unregister_func();
            window.onbeforeunload = null;
        });

        // Ask user when reloading/closing if unsaved changes
        window.onbeforeunload = (event) => {
            if (this.config.app.user_confirmation_to_discard_changes && this.isInterpretationOngoing() && this.selected_interpretation.dirty) { // TODO: create switch to disable in CI/test
                event.returnValue = "You have unsaved work. Do you really want to exit application?";
            }
        };
    }

    _setWatchers(rootScope) {
        // Watch interpretation's state/user_state and call update whenever it changes
        let watchStateFn = () => {
            if (this.isInterpretationOngoing() &&
                this.selected_interpretation.state) {
                return this.selected_interpretation.state;
            }
        };
        let watchUserStateFn = () => {
            if (this.isInterpretationOngoing() &&
                this.selected_interpretation.user_state) {
                return this.selected_interpretation.user_state;
            }
        };
        this.rootScope.$watch(watchStateFn, (n, o) => {
            // If no old object, we're on the first iteration
            // -> don't set dirty
            if (this.selected_interpretation && o) {
                this.selected_interpretation.setDirty();
            }
        }, true); // true -> Deep watch

        this.rootScope.$watch(watchUserStateFn, (n, o) => {
            if (this.selected_interpretation && o) {
                this.selected_interpretation.setDirty();
            }
        }, true); // true -> Deep watch


        this.rootScope.$watch(
            () => this.getInterpretation(),
            () => this._loadAllele(this.selected_interpretation)
        );
    }

    setupNavbar() {
        if (this.getAlleles().length) {
            this.navbar.replaceItems([
                {
                    title: `${this.getAlleles()[0].toString()} ${this.genepanelName}_${this.genepanelVersion}`,
                    url: "/overview"
                }
            ]);
            this.navbar.setAllele(this.getAlleles()[0]);
        }
    }

    confirmAbortInterpretation(event) {
        if (this.isInterpretationOngoing() && !event.defaultPrevented) {
            let choice = confirm('Abort current analysis? Any unsaved changes will be lost!');
            if (!choice) {
                event.preventDefault();
            }
        }
    }

    getInterpretation() {
        // Force selected interpretation to be the Ongoing one, if it exists, to avoid mixups.
        let ongoing_interpretation = this.interpretations.find(i => i.status === 'Ongoing');
        if (ongoing_interpretation) {
            this.selected_interpretation = ongoing_interpretation;
        }

        if (this.selected_interpretation) {
            return this.selected_interpretation;
        }
        return this.dummy_interpretation;
    }

    getAlleles() {
        if (this.interpretations.length && this.selected_interpretation) {
            return this.selected_interpretation_alleles;
        }
        // Fall back to this.allele when no interpretation exists on backend
        return this.alleles;
    }

    isInterpretationOngoing() {
        let interpretation = this.getInterpretation();
        return interpretation && interpretation.status === 'Ongoing';
    }

    showHistory() {
        return !this.isInterpretationOngoing()
               && this.history_interpretations.length;
    }

    reloadInterpretationData() {
        this._loadInterpretations().then(() => {
            this.history_interpretations = this.interpretations.filter(i => i.status === 'Done');
            let last_interpretation = this.interpretations[this.interpretations.length-1];

            // If an interpretation is Ongoing, we assign it directly
            if (last_interpretation && last_interpretation.status === 'Ongoing') {
                this.selected_interpretation = last_interpretation;
            }
            // Otherwise, select the last item of the dropdown to show latest history as default
            else if (this.history_interpretations.length) {
                this.selected_interpretation = this.history_interpretations[this.history_interpretations.length-1];
            }
            else {
                this.selected_interpretation = null;
            }
            this.interpretations_loaded = true;
            console.log("Reloaded interpretation data:", this.selected_interpretation)
        });
    }

    _loadAllele(interpretation) {
        this.alleles_loaded = false;
        this.selected_interpretation_alleles = null;
        if (this.allele_id && interpretation) {
            return this.workflowService.loadAlleles(
                'allele',
                this.allele_id,
                interpretation,
            ).then(alleles => {
                this.selected_interpretation_alleles = alleles;
                this.alleles_loaded = true;
            });
        }
    }

    _loadInterpretations() {
        return this.workflowResource.getInterpretations('allele', this.allele_id).then(interpretations => {
            this.interpretations = interpretations;
        });
    }

    _getQueryFromSelector() {
        let parts = this.variantSelector.split('-');
        if (parts.length !== 5) {
            throw Error("Variant selector doesn't contain 5 items")
        }
        let [chr, start, end, from, to] = parts;
        let query = {
            chromosome: chr,
            start_position: start,
            open_end_position: end,
            change_from: from,
            change_to: to
        }
        return query;
    }

    loadAlleleId() {
        let q = this._getQueryFromSelector();
        return this.alleleResource.getByQuery(q, null, this.genepanelName, this.genepanelVersion).then(a => {
            this.allele_id = a[0].id;
            this.alleles = a;
        });
    }

}
