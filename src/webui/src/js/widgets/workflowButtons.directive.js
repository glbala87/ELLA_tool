/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';
import {hasDataAtKey} from "../util";

@Directive({
    selector: 'workflow-buttons',
    scope: {
        alleles: '=',
        alleleId: '=?', // If allele workflow
        analysisId: '=?', // If analysis workflow
        genepanelName: '=?',
        genepanelVersion: '=?',
        readOnly: '=',
        startWhenReopen: '=?' // Reopen and start analysis at the same time
    },
    templateUrl: 'ngtmpl/workflowButtons.ngtmpl.html'
})
@Inject('Workflow', 'Config', 'User', 'Interpretation', 'InterpretationOverrideModal', '$location', 'toastr')
export class WorkflowButtonsController {
    constructor(Workflow, Config, User, Interpretation, InterpretationOverrideModal, $location, toastr) {
        this.workflowService = Workflow;
        this.config = Config.getConfig();
        this.user = User;
        this.interpretationService = Interpretation;
        this.interpretationOverrideModal = InterpretationOverrideModal;
        this.location = $location;
        this.toastr = toastr;
        this.interpretationUpdateInProgress = false;

        this.saveButtonOptions = {
            save: {
                text: 'Save'
            },
            'Not ready': {
                text: 'Start not ready'
            },
            'Interpretation': {
                text: 'Start interpretation'
            },
            'Review': {
                text: 'Start review'
            },
            'Medical review': {
                text: 'Start med. review'
            },
            reopen: {
                text: 'Reopen'
            },
            override: {
                text: 'Reassign to me'
            }
        };

    }

    getTypeAndId() {
        return [this.interpretationService.type, this.interpretationService.id]
    }

    getGenepanel() {
        return this.interpretationService.getGenepanel()
    }

    getAlleles() {
        return this.interpretationService.getAlleles()
    }

    _callReload() {
        let [type, id] = this.getTypeAndId()
        let genepanel = this.getGenepanel()
        this.interpretationService.load(type, id, genepanel.name, genepanel.version)
    }

    /**
     * Handles start/save button logic.
     * Start logic:
     * If no selectedInterpretation, but interpretations > 1, we need to reopen workflow
     * using the reopen actions. If not, just call start action.
     *
     * Save logic:
     * Just call save on workflowService.
     * Only works if there is a selectedInterpretation with status 'Ongoing'.
     *
     */
    clickStartSaveBtn() {
        let [type, id] = this.getTypeAndId();
        let selectedInterpretation = this.getSelectedInterpretation()
        // Reassign/save mode
        if (selectedInterpretation && selectedInterpretation.status === 'Ongoing') {
            if (selectedInterpretation.user.id !== this.user.getCurrentUserId()) {
                this.interpretationOverrideModal.show().then(result => {
                    if (result) {
                        this.workflowService.override(type, id).then(() => this._callReload());
                    }
                });
            }
            else {
                return this.workflowService.save(type, id, selectedInterpretation).then(() => {
                    this.interpretationUpdateInProgress = false;
                }).catch((error) => {
                    if (error.status === 409) {
                        this.toastr.error("Save failed: "+error.data);
                    } else {
                        this.toastr.error("Something went wrong while saving your work. To avoid losing it, please don't close this window and contact support.");
                    }
                    throw error;
                });
            }
        }
        else {
            let interpretations = this.getAllInterpretations()
            let genepanel = this.getGenepanel()
            // Call reopen if applicable
            if (interpretations.length && interpretations.every(i => i.status === 'Done')) {
                this.workflowService.reopen(type, id).then(() => {
                    if (this.startWhenReopen) {
                        this.workflowService.start(type, id, genepanel.name, genepanel.version).then(() => this._callReload());
                    }
                    else {
                        this._callReload();
                    }
                });
            }
            // Else start interpretation
            else {
                this.workflowService.start(type, id, genepanel.name, genepanel.version).then(() => this._callReload());
            }
        }
    }

    clickFinishBtn() {
        let [type, id] = this.getTypeAndId();
        let selectedInterpretation = this.getSelectedInterpretation()
        let historyInterpretations = this.interpretationService.getHistory();
        this.workflowService.checkFinishAllowed(type, id, selectedInterpretation, this.getAnalysis()).then(() => {
            this.workflowService.confirmCompleteFinalize(type, id, selectedInterpretation, this.getAlleles(), this.getAnalysis(), this.config, historyInterpretations).then((redirect) => {
                if (redirect) {
                    this.location.path('/overview');
                }
            }).catch((error) => {
                if (error && error.data) {
                    this.toastr.error("Finish not allowed: " + error.data)
                }
            })
        }).catch((error) => {
            this.toastr.error("Finish not allowed: " + error.data)
        })
    }

    showFinishBtn() {
        let selectedInterpretation = this.getSelectedInterpretation()
        if (selectedInterpretation && selectedInterpretation.status === 'Ongoing') {
                return selectedInterpretation.user.id === this.user.getCurrentUserId();
        }
        return false;
    }

    showStartBtn() {
        let user_config = this.config.user.user_config
        let [type, id] = this.getTypeAndId()
        return hasDataAtKey(user_config, "workflows", type, "can_start") ?
            Boolean(user_config.workflows[type].can_start) :
            true; // default
    }

    _getSaveStatus() {
        let interpretations = this.getAllInterpretations()
        if (!interpretations || !interpretations.length) {
            return 'Interpretation';
        }

        if (interpretations.find(i => {
            return i.status === 'Ongoing' &&
                   i.user.id !== this.user.getCurrentUserId();
        })) {
            return 'override';
        }

        if (interpretations.find(i => i.status === 'Ongoing')) {
            return 'save';
        }

        let not_started = interpretations.find(i => i.status === 'Not started');
        if (not_started) {
            return not_started.workflow_status
        }
        if (interpretations.length &&
            interpretations.every(i => i.status === 'Done')) {
            return 'reopen';
        }

        return 'Interpretation';
    }

    getSaveBtnText() {
        let status = this._getSaveStatus();
        if (status === 'reopen' && this.startWhenReopen) {
            // If we're going to start directly when reopening, show 'start' instead
            return this.saveButtonOptions['start'].text;
        }
        return this.saveButtonOptions[status].text;
    }

    getSaveBtnClass() {
        let classes = [];
        if (['Not ready', 'Interpretation', 'Review', 'Medical review'].includes(this._getSaveStatus())) {
            classes.push('green');
        }
        else if (['override'].includes(this._getSaveStatus())) {
            classes.push('red');
        }
        else {
            if (this.getSelectedInterpretation() &&
                this.getSelectedInterpretation().dirty) {
                classes.push('pink');
            }
            else {
                classes.push('blue');
            }
        }
        return classes;
    }

    getSelectedInterpretation() {
        return this.interpretationService.getSelected()
    }

    getAllInterpretations() {
        return this.interpretationService.getAll()
    }

    getAnalysis() {
        return this.interpretationService.getAnalysis()
    }


}
