/* jshint esnext: true */

/**
 * View for handling allele workflow.
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
import {STATUS_ONGOING, STATUS_NOT_STARTED} from '../../model/interpretation'
import {deepCopy} from '../../util'


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
    'GenepanelResource',
    'Allele',
    'Workflow',
    'Interpretation',
    'Navbar',
    'Config',
    'User',
    '$filter',
    'toastr')
export class WorkflowAlleleController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                GenepanelResource,
                Allele,
                Workflow,
                Interpretation,
                Navbar,
                Config,
                User,
                filter,
                toastr) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.genepanelResource = GenepanelResource;
        this.alleleService = Allele;
        this.workflowService = Workflow;
        this.interpretationService = Interpretation;
        this.navbar = Navbar;
        this.config = Config.getConfig();
        this.user = User;
        this.filter = filter;
        this.toastr = toastr;

        this.components = [ // instantiated/rendered in AlleleSectionboxContentController
            {
                name: 'classification',
                title: 'Classification',
                sections: [
                    {
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
                            placeholder: 'REPORT',
                            name: 'report'
                        },
                        content: [
                            {'tag': 'allele-info-acmg-selection'},
                            {'tag': 'allele-info-vardb'}
                        ],
                    },
                    {   name: 'frequency',
                        title: 'Frequency & QC',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
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
                            {'tag': 'allele-info-dbsnp'}
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
                        title: 'Studies & References',
                        options: {
                            hide_controls_on_collapse: true
                        },
                        controls: [
                            'references',
                            'add_acmg'
                        ],
                        alleleassessment_comment: {
                            placeholder: 'STUDIES-COMMENTS',
                            name: 'reference'
                        },
                        content: [
                            {'tag': 'allele-info-unpublished-references'},
                            {'tag': 'allele-info-published-references'}
                        ],
                    }
                ]
            }
        ];

        this.selected_component = this.components[0];

        this.collisionWarning = null;

        this.setUpListeners();

        this.scope.$watch(
            () => this.getGenepanel(),
            () => this.setupNavbar()
        )

        this.scope.$watch(
            () => this.interpretationService.genepanel_options_selected,
            () => {
                if (this.interpretationService.genepanel_options_selected) {
                    if (this.allele_id) {
                        this.reloadInterpretationData()
                    }
                }
            }
        )

        this.loadAlleleId().then(() => {
            this.checkForCollisions();
            if (!this.genepanelName || !this.genepanelVersion) {
                this.loadGenepanelOptions().then(() => {
                    this.reloadInterpretationData();
                })
            }
            else {
                this.reloadInterpretationData()
            }

        });
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
        if (this.getAlleles() && this.getAlleles().length) {
            let genepanel = this.getGenepanel()
            if (genepanel) {
                let label = `${genepanel.name} ${genepanel.version}`;
                this.navbar.replaceItems([
                    {
                        title: label,
                    }
                ])

                this.navbar.setAllele(this.getAlleles()[0], this.getGenepanel());
            }
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

    showHistory() {
        return !this.isInterpretationOngoing() && this.getHistory().length
    }

    formatHistoryOption(interpretation) {
        /// TODO: Move to filter
        if (interpretation.current) {
            return 'Current data';
        }
        let interpretation_idx = this.getAllInterpretations().indexOf(interpretation) + 1;
        let interpretation_date = this.filter('date')(interpretation.date_last_update, 'dd-MM-yyyy HH:mm');
        return `${interpretation_idx} • ${interpretation.user.full_name} • ${interpretation_date}`;
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

    loadGenepanelOptions() {
        return this.workflowResource.getGenepanels('allele', this.allele_id).then(genepanels => {
            this.genepanelOptions = genepanels;
            this.interpretationService.setGenepanelOptions(genepanels)
        })
    }

    checkForCollisions() {
        this.workflowResource.getCollisions('allele', this.allele_id).then(result => {
            if (result.length > 0) {
                let html = `<h4>This variant is currently `
                if (result.length === 1) {
                    html += `${result[0].user ? 'being worked on by ' + result[0].user.full_name : 'in review'} `
                    html += "in another workflow.</h4>"
                } else {
                    html += "being worked on in other workflows.<h4>"
                    for (let c of result) {
                        html += `<h3> ${c.type === 'analysis' ? 'Analysis' : 'Variant'}`
                        html += ` ${c.user ? "by "+c.user.full_name : 'in review'}</h3>`
                    }
                }

                this.collisionWarning = this.toastr.warning(html, {"timeOut": 0, "extendedTimeOut": 0, 'allowHtml': true, 'tapToDismiss': false, 'messageClass': 'toast-message-collision'})
            }
        });
    }

    getCollisionWarningHeight() {
        return this.collisionWarning.el[0].offsetHeight + 'px';
    }

    loadAlleleId() {
        let q = this._getQueryFromSelector();
        return this.alleleService.getAllelesByQuery(q, null, this.genepanelName, this.genepanelVersion).then(a => {
            this.allele_id = a[0].id;
        });
    }

    //
    // Trigger actions in interpretation service
    //
    reloadInterpretationData() {
        let gp_name, gp_version;
        if (this.genepanelName && this.genepanelVersion) {
            gp_name = this.genepanelName
            gp_version = this.genepanelVersion
        }
        else {
            gp_name = this.interpretationService.genepanel_options_selected.name
            gp_version = this.interpretationService.genepanel_options_selected.version
        }
        return this.interpretationService.load("allele", this.allele_id, gp_name, gp_version).then(() => {
            // Options will have been reset
            if ((!this.genepanelName || !this.genepanelVersion) &&
                this.genepanelOptions) {
                this.interpretationService.setGenepanelOptions(this.genepanelOptions)
            }
        })
    }

    //
    // Get data from interpretation service
    //
    isViewReady() {
        return this.interpretationService.isViewReady
    }

    getHistory() {
        return this.interpretationService.getHistory()
    }

    getSelectedInterpretation() {
        return this.interpretationService.getSelected()
    }

    getAllInterpretations() {
        return this.interpretationService.getAll();
    }

    getAlleles() {
        return this.interpretationService.getAlleles()
    }

    getGenepanel() {
        return this.interpretationService.getGenepanel()
    }

    isInterpretationOngoing() {
        return this.interpretationService.isOngoing()
    }

    readOnly() {
        return this.interpretationService.readOnly()
    }


}
