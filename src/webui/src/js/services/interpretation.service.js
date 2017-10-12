/* jshint esnext: true */


import {Service, Inject} from '../ng-decorators';
import {STATUS_ONGOING, STATUS_NOT_STARTED} from '../model/interpretation'
import {deepCopy} from '../util'

@Service({
    serviceName: 'Interpretation'
})
@Inject('$rootScope', 'WorkflowResource', 'Workflow')
class InterpretationService {

    constructor($rootScope, WorkflowResource, Workflow) {
        // this.resource = resource;
        this.rootScope = $rootScope;
        this.workflowResource = WorkflowResource;
        this.workflowService = Workflow;

        // this.dummy_interpretation = { // Dummy data for letting the user browse the view before starting interpretation. Never stored!
        //     genepanel_name: this.genepanelName,
        //     genepanel_version: this.genepanelVersion,
        //     dirty: false,
        //     state: {},
        //     user_state: {},
        //     status: STATUS_NOT_STARTED
        // };

    }

    resetInterpretations() {
        this.selected_interpretation = null; // Holds displayed interpretation
        this.selected_interpretation_alleles = []; // Loaded allele for current interpretation (annotation etc data can change based on interpretation snapshot)
        this.selected_interpretation_genepanel = null; // Loaded genepanel for current interpretation (used in navbar)
        this.alleles_loaded = false;  // Loading indicators etc

        this.collisions = null;

        this.interpretations = []; // Holds interpretations from backend
        this.history_interpretations = []; // Filtered interpretations, containing only the finished ones. Used in dropdown
        this.interpretations_loaded = false; // For hiding view until we've checked whether we have interpretations
        this.type = null;
        this.id = null;
    }

    /**
     * Loads interpretations from backend and sets:
     * - selected_interpretation
     * - history_interpretations
     * - interpretations
     */
    loadInterpretations(type, id) {
        this.resetInterpretations()
        console.log(type, id)
        if (type === "analysis") {
            return this.workflowResource.getInterpretations(type, id).then(interpretations => {
                this.type = type;
                this.id = id;
                this.interpretations = interpretations;
                console.log(this.interpretations)
                let done_interpretations = this.interpretations.filter(i => i.status === 'Done');
                let last_interpretation = this.interpretations[this.interpretations.length - 1];
                // If an interpretation is Ongoing, we assign it directly
                if (last_interpretation && last_interpretation.status === 'Ongoing') {
                    this.selected_interpretation = last_interpretation;
                    this.selected_interpretation.current = true;
                    this.history_interpretations = done_interpretations;
                }
                // Otherwise, make a copy of the last historical one to act as "current" entry.
                // Current means get latest allele data (instead of historical)
                // We make a copy, to prevent the state of the original to be modified
                else if (done_interpretations.length) {
                    let current_entry_copy = deepCopy(done_interpretations[done_interpretations.length - 1]);
                    current_entry_copy.current = true;
                    this.selected_interpretation = current_entry_copy;
                    this.history_interpretations = done_interpretations.concat([current_entry_copy]);
                }
                // If we have no history, set selected to null
                else {
                    this.selected_interpretation = last_interpretation;
                    this.history_interpretations = [];
                }
                // this.interpretations_loaded = true;
                console.log('(Re)Loaded ' + interpretations.length + ' interpretations');
                console.log('Setting selected interpretation:', this.selected_interpretation);


                //     this.history_interpretations = this.interpretations.filter(i => i.status === 'Done');
                //     let last_interpretation = this.interpretations[this.interpretations.length-1];
                //     // If an interpretation is Ongoing, we assign it directly
                //     if (last_interpretation.status === 'Ongoing') {
                //         this.selected_interpretation = last_interpretation;
                //     }
                //     // Otherwise, make a copy of the last historical one to act as "current" entry.
                //     // Current means get latest allele data (instead of historical)
                //     // We make a copy, to prevent the state of the original to be modified
                //     else if (this.history_interpretations.length) {
                //         this.selected_interpretation = deepCopy(this.history_interpretations[this.history_interpretations.length-1]);
                //         this.selected_interpretation.current = true;
                //         this.history_interpretations.push(this.selected_interpretation);
                //     }
                //     // If we have no history, select the last interpretation
                //     else {
                //         this.selected_interpretation = last_interpretation;
                //     }
                //     console.log("Reloaded interpretation data:", this.selected_interpretation)
                // });

            });
        } else {

            return this.workflowResource.getInterpretations('allele', id).then(interpretations => {
                this.type = "allele"
                this.id = id;
                this.interpretations = interpretations;
                let done_interpretations = this.interpretations.filter(i => i.status === 'Done');
                let last_interpretation = this.interpretations[this.interpretations.length - 1];
                // If an interpretation is Ongoing, we assign it directly
                if (last_interpretation && last_interpretation.status === 'Ongoing') {
                    this.selected_interpretation = last_interpretation;
                    this.selected_interpretation.current = true;
                    this.history_interpretations = done_interpretations;
                }
                // Otherwise, make a copy of the last historical one to act as "current" entry.
                // Current means get latest allele data (instead of historical)
                // We make a copy, to prevent the state of the original to be modified
                else if (done_interpretations.length) {
                    let current_entry_copy = deepCopy(done_interpretations[done_interpretations.length - 1]);
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
    }

    getSelectedInterpretation() {
        return this.selected_interpretation;

    }

    getAllInterpretations() {
        console.log("interpretationService.interpretations: ", this.interpretations)
        return this.interpretations;
    }

    getAlleles() {

    }

    getInterpretationHistory() {
        return this.history_interpretations;
    }

    loadAlleles() {
        if (this.selected_interpretation) {
                return this.workflowService.loadAlleles(
                    'analysis',
                    this.id,
                    this.selected_interpretation,
                    this.selected_interpretation.current // Whether to show current allele data or historical data
                ).then(alleles => {
                    this.selected_interpretation_alleles = alleles;
                    this.alleles_loaded = true;
                    console.log("(Re)Loaded alleles...", this.selected_interpretation_alleles);
                });
            }
        //
        // if (this.selected_interpretation) {
        //     return this.workflowService.loadAlleles(
        //         'analysis',
        //         this.analysisId,
        //         this.selected_interpretation,
        //         this.selected_interpretation.current // Whether to show current allele data or historical data
        //     ).then(alleles => {
        //         this.selected_interpretation_alleles = alleles;
        //         this.alleles_loaded = true;
        //         console.log("(Re)Loaded alleles...", this.selected_interpretation_alleles);
        //     });
        // }
    }

    isInterpretationOngoing() {
        let interpretation = this.getInterpretation();
        return interpretation && interpretation.status === 'Ongoing';
    }

    getGenepanel() {

    }

    getExcludedAlleleCount() {
        if (this.selected_interpretation) {
            return Object.values(this.selected_interpretation.excluded_allele_ids)
                .map(excluded_group => excluded_group.length)
                .reduce((total_length, length) => total_length + length);
        }
    }

    readOnly() {
        let interpretation = this.getInterpretation();
        if (!interpretation) {
            return true;
        }

        return !this.isInterpretationOngoing() || interpretation.user.id !== this.user.getCurrentUserId() ;

    }

    setupNavbar() {
        if (this.getAlleles().length) {
            this.navbar.replaceItems([this.genepanelName+" "+this.genepanelVersion]);
            // this.navbar.setAllele(this.getAlleles()[0], this.selected_interpretation_genepanel);
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


    getInterpretation(index) {
        if (!this.interpretations) return;
        if (index === undefined) {
            // Force selected interpretation to be the Ongoing one, if it exists, to avoid mixups.
            let ongoing_interpretation = this.interpretations.find(i => i.isOngoing());
            if (ongoing_interpretation) {
                this.selected_interpretation = ongoing_interpretation;
            }
        } else {
            // Get interpretation at index
        }

        return this.selected_interpretation ? this.selected_interpretation : undefined;
    }

    getAlleles() {
        if (this.interpretations && this.interpretations.length && this.selected_interpretation) {
            return this.selected_interpretation_alleles;
        }
        // Fall back to this.allele when no interpretation exists on backend
        // return this.alleles;


    }

    isInterpretationOngoing() {
        let interpretation = this.getInterpretation();
        return interpretation && interpretation.status === 'Ongoing';
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
                    console.log("(Re)Loaded alleles using interpretation "
                        +  this.selected_interpretation.id
                        + "(" + this.selected_interpretation.current + ")"
                        , this.selected_interpretation_alleles);
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


}
