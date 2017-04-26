/* jshint esnext: true */

/**
 * View for handling analysis workflow.
 *
 * The interpretation handling is a bit messy, and could be improved upon.
 * Basic idea:
 * - Get list of interpretations from backend.
 *  - If one is ongoing, show that one.
 *  - If all are done:
 *      - By default, create a 'current' interpretation, which is a copy of the latest interpretation.
 *        This is done in order to present the user with the latest data, i.e. how the view would look like
 *        if they started a new round. We need to make a copy, since the view might change the state of the object.
 *      - If selecting one of the historical ones (i.e. not the copy mentioned above), we load in the historical
 *        data to show the view like they user saw it at that point of time.
 */

import {Directive, Inject} from '../../ng-decorators';
import {deepCopy} from '../../util'

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
    'GenepanelResource',
    'AnalysisResource',
    'Workflow',
    'Navbar',
    'Config',
    'User',
    'AddExcludedAllelesModal',
    'clipboard',
    'toastr',
    '$filter')
export class AnalysisController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                GenepanelResource,
                AnalysisResource,
                Workflow,
                Navbar,
                Config,
                User,
                AddExcludedAllelesModal,
                clipboard,
                toastr,
                filter) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.genepanelResource = GenepanelResource;
        this.analysisResource = AnalysisResource;
        this.workflowService = Workflow;
        this.addExcludedAllelesModal = AddExcludedAllelesModal;
        this.analysis = null;
        this.active_interpretation = null;
        this.navbar = Navbar;
        this.config = Config.getConfig();
        this.user = User;
        this.clipboard = clipboard;
        this.toastr = toastr;
        this.filter = filter;

        this.components = [ // instantiated/rendered in AlleleSectionboxContentController
            {
                title: 'Classification',
                sections: [
                    {
                        name: 'classification',
                        title: 'Classification',
                        options: {
                            hide_controls_on_collapse: false,
                            show_included_acmg_codes: true
                        },
                        controls: [
                            'collapse_all',
                            'add_acmg',
                            'classification',,
                            'reuse_classification'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'EVALUATION',
                            name: 'classification'
                        },
                        report_comment: {
                            placeholder: 'REPORT'
                        },
                        content: [
                            {'tag': 'allele-info-acmg-selection'},
                            {'tag': 'allele-info-vardb'}
                        ],
                    },
                    {
                        name: 'frequency',
                        title: 'Frequency & QC',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
                            'igv',
                            'copy_alamut',
                            'toggle_class1',
                            'toggle_class2',
                            'toggle_technical',
                            'add_acmg'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'FREQUENCY-COMMENTS',
                            name: 'frequency'
                        },
                        content: [
                            {'tag': 'allele-info-frequency-exac'},
                            {'tag': 'allele-info-frequency-thousandg'},
                            {'tag': 'allele-info-frequency-indb'},
                            {'tag': 'allele-info-dbsnp'},
                            {'tag': 'allele-info-quality'},
                        ],
                    },
                    {
                        name: 'external',
                        title: 'External',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
                            'custom_external',
                            'add_acmg'
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
                        name: 'prediction',
                        title: 'Prediction',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
                            'custom_prediction',
                            'add_acmg'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'PREDICTION-COMMENTS',
                            name: 'prediction'
                        },
                        content: [
                            {'tag': 'allele-info-consequence'},
                            {'tag': 'allele-info-prediction-other'},
                        ],
                    },
                    {
                        name: 'references',
                        title: 'References',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
                            'references',
                            'add_acmg'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'REFERENCE-COMMENTS',
                            name: 'reference'
                        },
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

        this.selected_interpretation = null; // Holds displayed interpretation
        this.selected_interpretation_alleles = []; // Loaded alleles for current interpretation
        this.alleles_loaded = false;  // Loading indicators etc

        this.allele_collisions = null;

        this.interpretations = []; // Holds interpretations from backend
        this.history_interpretations = []; // Filtered interpretations, containing only the finished ones. Used in dropdown

        this.setUpListeners();
        this._setWatchers();
        this.setupNavbar();

        this._loadAnalysis();
        this.reloadInterpretationData();
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
            () => this.selected_interpretation,
            () => {
                this.alleles_loaded = false;  // Make <interpretation> redraw
                this.loadAlleles()
            }
        );
    }

    setupNavbar() {
        let label = this.analysis ? this.analysis.name : '';
        this.navbar.replaceItems([
            {
                title: label,
                url: "/overview/analyses"
            }
        ]);
    }

    getExcludedAlleleCount() {
        if (this.selected_interpretation) {
            return Object.values(this.selected_interpretation.excluded_allele_ids)
                .map(excluded_group => excluded_group.length)
                .reduce((total_length, length) => total_length + length);
        }
    }

    /**
     * Popups a dialog for adding excluded alleles
     */
    modalAddExcludedAlleles() {
        if (this.getInterpretation().state.manuallyAddedAlleles === undefined) {
            this.getInterpretation().state.manuallyAddedAlleles = [];
        }
        this.addExcludedAllelesModal.show(
            this.getInterpretation().excluded_allele_ids,
            this.getInterpretation().state.manuallyAddedAlleles,
            this.analysis.samples[0].id, // FIXME: Support multiple samples
            this.getInterpretation().genepanel_name,
            this.getInterpretation().genepanel_version,
            this.readOnly()
        ).then(added => {
            if (this.isInterpretationOngoing()) { // noop if analysis is finalized
                // Uses the result of modal as it's more excplicit than mutating the inputs to the show method
                this.getInterpretation().state.manuallyAddedAlleles = added;
                this.loadAlleles(this.selected_interpretation);
            }
        }).catch(() => {
            this.loadAlleles(this.selected_interpretation);  // Also update on modal dismissal
        });
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

        return this.selected_interpretation;
    }

    isInterpretationOngoing() {
        let interpretation = this.getInterpretation();
        return interpretation && interpretation.status === 'Ongoing';
    }

    readOnly() {
        let interpretation = this.getInterpretation();
        if (!interpretation) {
            return true;
        }

        return !this.isInterpretationOngoing() || interpretation.user.id !== this.user.getCurrentUserId() ;

    }


    showHistory() {
        return !this.isInterpretationOngoing()
               && this.history_interpretations.length;
    }

    formatHistoryOption(interpretation) {
        if (interpretation.current) {
            return 'Current data';
        }
        let interpretation_idx = this.interpretations.indexOf(interpretation) + 1;
        let interpretation_date = this.filter('date')(interpretation.date_last_update, 'dd-MM-yyyy HH:mm');
        return `${interpretation_idx} • ${interpretation.user.first_name} ${interpretation.user.last_name} • ${interpretation_date}`;
    }

    reloadInterpretationData() {
        this._loadInterpretations().then(() => {
            this.history_interpretations = this.interpretations.filter(i => i.status === 'Done');
            let last_interpretation = this.interpretations[this.interpretations.length-1];
            // If an interpretation is Ongoing, we assign it directly
            if (last_interpretation.status === 'Ongoing') {
                this.selected_interpretation = last_interpretation;
            }
            // Otherwise, make a copy of the last historical one to act as "current" entry.
            // Current means get latest allele data (instead of historical)
            // We make a copy, to prevent the state of the original to be modified
            else if (this.history_interpretations.length) {
                this.selected_interpretation = deepCopy(this.history_interpretations[this.history_interpretations.length-1]);
                this.selected_interpretation.current = true;
                this.history_interpretations.push(this.selected_interpretation);
            }
            // If we have no history, select the last interpretation
            else {
                this.selected_interpretation = last_interpretation;
            }
            console.log("Reloaded interpretation data:", this.selected_interpretation)
        });
    }

    loadAlleles() {
        if (this.selected_interpretation) {
            return this.workflowService.loadAlleles(
                'analysis',
                this.analysisId,
                this.selected_interpretation,
                this.selected_interpretation.current // Whether to show current allele data or historical data
            ).then(alleles => {
                this.selected_interpretation_alleles = alleles;
                this.alleles_loaded = true;
                console.log("(Re)Loaded alleles...", this.selected_interpretation_alleles);
            });
        }
    }

    _loadInterpretations() {
        return this.workflowResource.getInterpretations('analysis', this.analysisId).then(interpretations => {
            this.interpretations = interpretations;
            console.log('Loaded ' + interpretations.length + ' interpretations');
        });
    }

    _loadAnalysis() {
        this.analysisResource.getAnalysis(this.analysisId).then(a => {
            this.analysis = a;
            this.setupNavbar();
            this.genepanelResource.get(a.genepanel.name, a.genepanel.version).then(gp => {
                this.genepanel = gp;
            });
        });

        this.workflowResource.getCollisions('analysis', this.analysisId).then(c => {
            this.allele_collisions = c;
        });
    }

    copyAlamut() {
        this.clipboard.copyText(
            this.selected_interpretation_alleles.map(a => a.formatAlamut() + '\n').join('')
        );
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }

}
