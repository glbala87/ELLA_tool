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
    'Navbar',
    'Config',
    'User',
    '$filter')
export class WorkflowAlleleController {
    constructor(rootScope,
                scope,
                WorkflowResource,
                GenepanelResource,
                Allele,
                Workflow,
                Navbar,
                Config,
                User,
                filter) {
        this.rootScope = rootScope;
        this.scope = scope;
        this.workflowResource = WorkflowResource;
        this.genepanelResource = GenepanelResource;
        this.alleleService = Allele;
        this.workflowService = Workflow;
        this.analysis = null;
        this.active_interpretation = null;
        this.navbar = Navbar;
        this.config = Config.getConfig();
        this.user = User;
        this.filter = filter;

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
                            'upload',
                            'collapse_all',
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
                            {'tag': 'allele-info-vardb'},
                            {'tag': 'allele-info-attachments'}
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
            }
        ];

        this.selected_component = this.components[0];

        this.alleles = []; // Holds allele based on directive params. Array since "everything" expects an array...

        this.selected_interpretation = null; // Holds displayed interpretation
        this.selected_interpretation_alleles = []; // Loaded allele for current interpretation (annotation etc data can change based on interpretation snapshot)
        this.selected_interpretation_genepanel = null; // Loaded genepanel for current interpretation (used in navbar)
        this.alleles_loaded = false;  // Loading indicators etc

        this.allele_collisions = null;

        this.interpretations = []; // Holds interpretations from backend
        this.history_interpretations = []; // Filtered interpretations, containing only the finished ones. Used in dropdown
        this.interpretations_loaded = false; // For hiding view until we've checked whether we have interpretations

        this.dummy_interpretation = { // Dummy data for letting the user browse the view before starting interpretation. Never stored!
            genepanel_name: this.genepanelName,
            genepanel_version: this.genepanelVersion,
            dirty: false,
            state: {},
            user_state: {},
            status: STATUS_NOT_STARTED
        };

        this.setUpListeners();
        this._setWatchers();

        this.loadAlleleId().then(() => {
            this.checkForCollisions();
            this.dummy_interpretation.allele_ids = [this.allele_id];
            this.reloadInterpretationData();
            this.loadGenepanel().then(() => {
                this.setupNavbar();
            });
        });
    }

    readOnly() {
        let interpretation = this.getInterpretation();
        if (!interpretation) {
            return true;
        }

        return !this.isInterpretationOngoing() || interpretation.user.id !== this.user.getCurrentUserId() ;

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
            if (this.isInterpretationOngoing() && this.selected_interpretation &&
                this.selected_interpretation.state) {
                return this.selected_interpretation.state;
            }
        };
        let watchUserStateFn = () => {
            if (this.isInterpretationOngoing() && this.selected_interpretation &&
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
            () => {
                this.alleles_loaded = false;
                let a = this.loadAllele();
                let g = this.loadGenepanel();  // Reload genepanel in case it was different
                Promise.all([a, g]).then(() => this.setupNavbar());
            }
        );
    }

    setupNavbar() {
        if (this.getAlleles().length) {
            let label = `${this.getAlleles()[0].toString()} ${this.genepanelName}_${this.genepanelVersion}`;
            this.navbar.replaceItems([
                {
                    title: label,
                    url: "/overview/variants"
                }
            ]);
            this.navbar.setAllele(this.getAlleles()[0], this.selected_interpretation_genepanel);
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
        let ongoing_interpretation = this.interpretations.find(i => i.isOngoing());
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

    formatHistoryOption(interpretation) {
        if (interpretation.current) {
            return 'Current data';
        }
        let interpretation_idx = this.interpretations.indexOf(interpretation) + 1;
        let interpretation_date = this.filter('date')(interpretation.date_last_update, 'dd-MM-yyyy HH:mm');
        return `${interpretation_idx} • ${interpretation.user.first_name} ${interpretation.user.last_name} • ${interpretation_date}`;
    }

    /**
     * Loads interpretations from backend and sets:
     * - selected_interpretation
     * - history_interpretations
     * - interpretations
     */
    reloadInterpretationData() {
        return this.workflowResource.getInterpretations('allele', this.allele_id).then(interpretations => {
            this.interpretations = interpretations;
            let done_interpretations = this.interpretations.filter(i => i.status === 'Done');
            let last_interpretation = this.interpretations[this.interpretations.length-1];
            // If an interpretation is Ongoing, we assign it directly
            if (last_interpretation && last_interpretation.status === 'Ongoing') {
                this.selected_interpretation = last_interpretation;
                this.history_interpretations = done_interpretations;
            }
            // Otherwise, make a copy of the last historical one to act as "current" entry.
            // Current means get latest allele data (instead of historical)
            // We make a copy, to prevent the state of the original to be modified
            else if (done_interpretations.length) {
                let current_entry_copy = deepCopy(done_interpretations[done_interpretations.length-1]);
                current_entry_copy.current = true;
                this.selected_interpretation = current_entry_copy;
                this.history_interpretations = done_interpretations.concat([current_entry_copy]);
            }
            // If we have no history, set selected to null
            else {
                this.selected_interpretation = null;
                this.history_interpretations = [];
            }
            this.interpretations_loaded = true;
            console.log('(Re)Loaded ' + interpretations.length + ' interpretations');
            console.log('Setting selected interpretation:', this.selected_interpretation);

        });
    }

    loadAllele() {
        this.alleles_loaded = false;
        if (this.allele_id && this.selected_interpretation) {
            return this.workflowService.loadAlleles(
                'allele',
                this.allele_id,
                this.selected_interpretation,
                this.selected_interpretation.current // Whether to show current allele data or historical data
            ).then(
                alleles => {
                    this.selected_interpretation_alleles = alleles;
                    this.alleles_loaded = true;
                    console.log("(Re)Loaded alleles...", this.selected_interpretation_alleles);
                },
                () => { this.selected_interpretation_alleles = []; } // On error

            );
        }
    }

    loadGenepanel() {
        let gp_name = this.genepanelName;
        let gp_version = this.genepanelVersion;
        if (this.selected_interpretation) {
            gp_name = this.selected_interpretation.genepanel_name;
            gp_version = this.selected_interpretation.genepanel_version;
        }
        return this.genepanelResource.get(gp_name, gp_version).then(
            gp => this.selected_interpretation_genepanel = gp
        );
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

    checkForCollisions() {
        this.workflowResource.getCollisions('allele', this.allele_id).then(c => {
            this.allele_collisions = c;
        });
    }

    loadAlleleId() {
        let q = this._getQueryFromSelector();
        return this.alleleService.getAllelesByQuery(q, null, this.genepanelName, this.genepanelVersion).then(a => {
            this.allele_id = a[0].id;
            return this.alleleService.updateACMG(a, this.genepanelName, this.genepanelVersion, []).then(
                () => this.alleles = a
            );
        });
    }


}
