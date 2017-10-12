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
    'Interpretation',
    'Navbar',
    'Config',
    'User',
    'AddExcludedAllelesModal',
    'clipboard',
    'toastr',
    '$filter')
export class WorkflowAnalysisController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                GenepanelResource,
                AnalysisResource,
                Workflow,
                Interpretation,
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
        this.interpretationService = Interpretation;
        this.addExcludedAllelesModal = AddExcludedAllelesModal;
        this.analysis = null;
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
                            'upload',
                            'add_acmg',
                            'classification',
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
                            {'tag': 'allele-info-vardb'},
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
                            {'tag': 'allele-info-frequency-gnomad-exomes'},
                            {'tag': 'allele-info-frequency-gnomad-genomes'},
                            {'tag': 'allele-info-frequency-exac'},
                            {'tag': 'allele-info-frequency-thousandg'},
                            {'tag': 'allele-info-frequency-indb'},
                            {'tag': 'allele-info-dbsnp'},
                            {'tag': 'allele-info-quality'}
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
                            {'tag': 'allele-info-unpublished-references'},
                            {'tag': 'allele-info-published-references'}
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

        this.alleles_loaded = false;  // Loading indicators etc

        this.collisionWarning = null;


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
            if (this.config.app.user_confirmation_on_state_change && this.isInterpretationOngoing() && this.getSelectedInterpretation().dirty) {
                this.confirmAbortInterpretation(event);
            }
        });

        // Unregister when scope is destroyed.
        this.scope.$on('$destroy', () => {
            if (this.collisionWarning) {
                this.toastr.clear(this.collisionWarning)
            }
            unregister_func();
            window.onbeforeunload = null;
        });

        // Ask user when reloading/closing if unsaved changes
        window.onbeforeunload = (event) => {
            if (this.config.app.user_confirmation_to_discard_changes && this.isInterpretationOngoing() && this.getSelectedInterpretation().dirty) { // TODO: create switch to disable in CI/test
                event.returnValue = "You have unsaved work. Do you really want to exit application?";
            }
        };
    }

    _setWatchers(rootScope) {
        // Watch interpretation's state/user_state and call update whenever it changes
        let watchStateFn = () => {
            if (this.isInterpretationOngoing() &&
                this.getSelectedInterpretation().state) {
                return this.getSelectedInterpretation().state;
            }
        };
        let watchUserStateFn = () => {
            if (this.isInterpretationOngoing() &&
                this.getSelectedInterpretation().user_state) {
                return this.getSelectedInterpretation().user_state;
            }
        };
        this.rootScope.$watch(watchStateFn, (n, o) => {
            // If no old object, we're on the first iteration
            // -> don't set dirty
            if (this.getSelectedInterpretation() && o) {
                this.getSelectedInterpretation().setDirty();
            }
        }, true); // true -> Deep watch

        this.rootScope.$watch(watchUserStateFn, (n, o) => {
            if (this.getSelectedInterpretation() && o) {
                this.getSelectedInterpretation().setDirty();
            }
        }, true); // true -> Deep watch


        this.rootScope.$watch(
            () => this.getSelectedInterpretation(),
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
                url: `/overview`
            }
        ]);
    }

    getExcludedAlleleCount() {
        if (this.getInterpretation()) {
            return Object.values(this.getInterpretation().excluded_allele_ids)
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
        return this.interpretationService.getInterpretation()
    }

    getSelectedInterpretation() {
        return this.interpretationService.getSelectedInterpretation()
    }

    getAllInterpretations() {
        return this.interpretationService.getAllInterpretations()
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
               && this.interpretationService.getInterpretationHistory().length;
    }

    getHistory() {
        return this.interpretationService.getInterpretationHistory()
    }

    formatHistoryOption(interpretation) {
        ///TODO: Move to filter
        if (interpretation.current) {
            return 'Current data';
        }
        let interpretation_idx = this.getAllInterpretations().indexOf(interpretation) + 1;
        let interpretation_date = this.filter('date')(interpretation.date_last_update, 'dd-MM-yyyy HH:mm');
        return `${interpretation_idx} • ${interpretation.user.full_name} • ${interpretation_date}`;
    }

    reloadInterpretationData() {
        this.interpretationService.loadInterpretations("analysis", this.analysisId)
    }

    loadAlleles() {

        this.alleles_loaded = false;
        let p = this.interpretationService.loadAlleles();
        if (p) {
            p.then( () => {
                this.alleles_loaded = true;
            })
        }
    }

    getAlleles() {
        return this.interpretationService.getAlleles()
    }

    _loadAnalysis() {
        this.analysisResource.getAnalysis(this.analysisId).then(a => {
            this.analysis = a;
            this.setupNavbar();
            this.genepanelResource.get(a.genepanel.name, a.genepanel.version).then(gp => {
                this.genepanel = gp;
            });
        });

        this.workflowResource.getCollisions('analysis', this.analysisId).then(result => {
            if (result.length > 0) {
                let html = "<h4>There "
                if (result.length > 1) {
                    html += `are currently ${result.length} variants being worked on in other workflows.</h4>`
                } else {
                    html += `is currently ${result.length} variant being worked on in another workflow.</h4>`
                }

                for (let c of result) {
                    html += `<h3> ${c.allele.annotation.filtered[0].symbol} ${c.allele.annotation.filtered[0].HGVSc_short}`
                    html += ` by ${c.user ? c.user.full_name : 'no user (IN REVIEW)'} (${c.type === 'analysis' ? 'ANALYSIS' : 'VARIANT'})</h3>`
                }

                this.collisionWarning = this.toastr.warning(html, {"timeOut": 0, "extendedTimeOut": 0, 'allowHtml': true, 'tapToDismiss': false, 'messageClass': 'toast-message-collision'})
            }
        });
    }

    copyAlamut() {
        this.clipboard.copyText(
            this.interpretationService.getAlleles().map(a => a.formatAlamut() + '\n').join('')
        );
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }

}
