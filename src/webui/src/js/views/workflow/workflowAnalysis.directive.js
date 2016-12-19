/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'workflow-analysis',
    scope: {
        'analysisId': '@'
    },
    templateUrl: 'ngtmpl/workflowAnalysis.ngtmpl.html'
})
@Inject('$rootScope',
    '$scope',
    'WorkflowResource',
    'AnalysisResource',
    'Workflow',
    'Navbar',
    'Config',
    'User')
export class AnalysisController {
    constructor(rootScope, scope, WorkflowResource, AnalysisResource, Workflow, Navbar, Config, User) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.analysisResource = AnalysisResource;
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
                        comments: [
                            {
                                placeholder: 'EVALUATION',
                                modeltype: 'alleleassessment',
                                modelname: 'classification'
                            },
                            {
                                placeholder: 'REPORT',
                                modeltype: 'report',
                                modelname: 'evaluation'
                            }
                        ],
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
                            'igv',
                            'copy_alamut',
                            'toggle_class1',
                            'toggle_class2',
                            'toggle_technical'
                        ],
                        comments: [
                            {
                                placeholder: 'FREQUENCY-COMMENTS',
                                modeltype: 'alleleassessment',
                                modelname: 'frequency'
                            }
                        ],
                        content: [
                            {'tag': 'allele-info-frequency-exac'},
                            {'tag': 'allele-info-frequency-thousandg'},
                            {'tag': 'allele-info-frequency-esp6500'},
                            {'tag': 'allele-info-frequency-indb'},
                            {'tag': 'allele-info-dbsnp'},
                            {'tag': 'allele-info-quality'},
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
                        comments: [
                            {
                                placeholder: 'EXTERNAL DB-COMMENTS',
                                modeltype: 'alleleassessment',
                                modelname: 'external'
                            }
                        ],
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
                        comments: [
                            {
                                placeholder: 'PREDICTION-COMMENTS',
                                modeltype: 'alleleassessment',
                                modelname: 'prediction'
                            }
                        ],
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
            },
            {
                title: 'Report',
                alleles: []
            }
        ];
        this.selected_component = this.components[0];

        // Dummy state provided to <interpretation> before we have loaded actual interpretation. Never stored, just discarded..
        // Let's user browse read only view, without starting interpretation
        this.dummy_interpretation = {
            state: {},
            user_state: {},
            allele_ids: [1, 2, 3]  // Debug: Remove me
        };
        this.current_interpretation = null; // Holds active interpretation for editing

        this.history_selected_interpretation = null; // Holds selected interpretation from history
        this.history_interpretations = []; // Holds interpretation history from backend

        this.setUpListeners();
        this._setWatchers();
        this.setupNavbar();

        this._loadAnalysis(this.analysisId);
        this.reloadInterpretationData();
    }

    setUpListeners() {
        // Setup listener for asking user if they really want to navigate
        // away from page if unsaved changes
        let unregister_func = this.rootScope.$on('$stateChangeStart', (event) => {  // TODO: create switch to disable in CI/test
            if (this.config.app.user_confirmation_on_state_change && this.interpretation && this.interpretation.dirty) {
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
            if (this.config.app.user_confirmation_to_discard_changes && this.interpretation && this.interpretation.dirty) { // TODO: create switch to disable in CI/test
                event.returnValue = "You have unsaved work. Do you really want to exit application?";
            }
        };
    }

    _setWatchers(rootScope) {
        // Watch interpretation's state/user_state and call update whenever it changes
        let watchStateFn = () => {
            if (this.interpretation &&
                this.interpretation.state) {
                return this.interpretation.state;
            }
        };
        let watchUserStateFn = () => {
            if (this.interpretation &&
                this.interpretation.user_state) {
                return this.interpretation.user_state;
            }
        };
        this.rootScope.$watch(watchStateFn, (n, o) => {
            // If no old object, we're on the first iteration
            // -> don't set dirty
            if (this.interpretation && o) {
                this.interpretation.setDirty();
            }
        }, true); // true -> Deep watch

        this.rootScope.$watch(watchUserStateFn, (n, o) => {
            if (this.interpretation && o) {
                this.interpretation.setDirty();
            }
        }, true); // true -> Deep watch
    }

    setupNavbar() {
        this.navbar.replaceItems([
            {
                title: this.analysis ? this.analysis.name : '',
                url: "/overview"
            }
        ]);
        this.navbar.setAnalysis(this.analysis);
    }

    getExcludedAlleleCount() {
        return Object.values(this.interpretation.excluded_allele_ids)
               .map(excluded_group => excluded_group.length)
               .reduce((total_length, length) => total_length + length);
    }

    /**
     * User chose an interpretation (round) (when read-only sample history)
     */
    onInterpretationRoundChange(value) {
        console.log("user chose " + value + ". Now this.manuallySelectedInterpretation = " + this.manuallySelectedInterpretation);
        this.workflowService.loadInterpretation(this.manuallySelectedInterpretation.id).then(i => {
            this.interpretation = i;
        }).catch((err) => {
            console.error(err);
        })
    }

    /**
     * Checks whether the loaded interpretation
     * is current user.
     * @return {Boolean} true if undefined or current user, false if different user
     */
    isCurrentUser() {
        if (!this.interpretation ||
            this.interpretation.user_id === undefined ||
            this.interpretation.user_id === null) {
            return true;
        }
        return this.interpretation.user_id === this.user.getCurrentUserId();
    }

    isAnalysisDone() {
        if (!this.interpretation) {
            return false;
        }

        return this.interpretation.status == 'Done';
    }

    confirmAbortInterpretation(event) {
        if (this.interpretation && !event.defaultPrevented) {
            let choice = confirm('Abort current analysis? Any unsaved changes will be lost!');
            if (!choice) {
                event.preventDefault();
            }
        }
    }

    getInterpretation() {
        if (this.current_interpretation &&
            (this.current_interpretation.status == 'Not started' ||
             this.current_interpretation.status ==  'Ongoing')
           ) {
            return this.current_interpretation;
        }
        else if (this.history_selected_interpretation) {
            return this.history_selected_interpretation;
        }
        return this.dummy_interpretation;
    }

    reloadInterpretationData() {
        console.log("Reloading interpretation data...")
        this._loadCurrentInterpretation(this.analysisId);
        this._loadHistoryInterpretations(this.analysisId);
    }

    _loadCurrentInterpretation(analysis_id) {
        return this.workflowResource.getAnalysisCurrentInterpretations(analysis_id).then(current => {
            console.log(current);
            this.current_interpretation = current;
        });
    }

    _loadHistoryInterpretations(analysis_id) {
        return this.workflowResource.getAnalysisInterpretations(analysis_id).then(interpretations =>
            this.history_interpretations = interpretations
        );
    }

    _loadAnalysis(analysis_id) {
        this.analysisResource.getAnalysis(analysis_id).then(a => {
            this.analysis = a;
            this.setupNavbar();
        });
    }

}
