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
        'analysisId': '='
    },
    templateUrl: 'ngtmpl/workflowAnalysis.ngtmpl.html'
})
@Inject('$rootScope',
    '$scope',
    'WorkflowResource',
    'Workflow',
    'Interpretation',
    'Navbar',
    'Config',
    'User',
    'toastr',
    '$filter')
export class WorkflowAnalysisController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                Workflow,
                Interpretation,
                Navbar,
                Config,
                User,
                toastr,
                filter) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.workflowService = Workflow;
        this.interpretationService = Interpretation;
        this.navbar = Navbar;
        this.config = Config.getConfig();
        this.user = User;
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
                            {
                                tag: 'allele-info-references',
                                attr: {
                                    title: 'Pending'
                                }
                            },
                            {
                                tag: 'allele-info-references',
                                attr: {
                                    title: 'Evaluated'
                                }
                            },
                            {
                                tag: 'allele-info-references',
                                attr: {
                                    title: 'Excluded'
                                }
                            }
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

        this.collisionWarning = null;

        this.setUpListeners();
        this.setupNavbar();


        this.reloadInterpretationData();
        this.checkForCollisions();

        this.scope.$watch(
            () => this.getAnalysis(),
            () => this.setupNavbar()
        )
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

    setupNavbar() {
        let analysis = this.getAnalysis()
        let label = analysis ? analysis.name : '';

        this.navbar.replaceItems([
            {
                title: label,
            }
        ]);
    }

    confirmAbortInterpretation(event) {
        if (this.isInterpretationOngoing() && !event.defaultPrevented) {
            let choice = confirm('Abort current analysis? Any unsaved changes will be lost!');
            if (!choice) {
                event.preventDefault();
            }
        }
    }

    checkForCollisions() {
        this.workflowResource.getCollisions('analysis', this.analysisId).then(result => {
            if (result.length > 0) {
                let html = "<h4>There "
                if (result.length > 1) {
                    html += `are currently ${result.length} variants being worked on in other workflows.</h4>`
                } else {
                    html += `is currently ${result.length} variant being worked on in another workflow.</h4>`
                }

                for (let c of result) {
                    html += `<h3> ${c.allele.annotation.filtered[0].symbol} ${c.allele.annotation.filtered[0].HGVSc_short || c.allele.getHGVSgShort()}`
                    html += ` ${c.user ? "by "+c.user.full_name : 'in review'} (${c.type === 'analysis' ? 'ANALYSIS' : 'VARIANT'})</h3>`
                }

                this.collisionWarning = this.toastr.warning(html, {"timeOut": 0, "extendedTimeOut": 0, 'allowHtml': true, 'tapToDismiss': false, 'messageClass': 'toast-message-collision'})
            }
        });
    }

    getCollisionWarningHeight() {
        return this.collisionWarning.el[0].offsetHeight + 'px';
    }

    //
    // Trigger actions in interpretation service
    //
    reloadInterpretationData() {
        this.interpretationService.load("analysis", this.analysisId, null, null)
    }

    loadAlleles() {
        return this.interpretationService.loadAlleles(true); // true => trigger redraw
    }

    //
    // Get data from interpretation service
    //
    getAlleles() {
        return this.interpretationService.getAlleles()
    }

    isViewReady() {
        return this.interpretationService.isViewReady && this.getAnalysis();
    }

    getSelectedInterpretation() {
        return this.interpretationService.getSelected()
    }

    getAllInterpretations() {
        return this.interpretationService.getAll()
    }

    isInterpretationOngoing() {
        return this.interpretationService.isOngoing()
    }

    readOnly() {
        return this.interpretationService.readOnly()
    }

    getInterpretationHistory() {
        return this.interpretationService.getHistory()
    }

    getAnalysis() {
        return this.interpretationService.getAnalysis()
    }
}
