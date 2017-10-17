/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

@Directive({
    selector: 'workflow-buttons',
    scope: {
        // selectedInterpretation: '=',
        // interpretations: '=',
        alleles: '=',
        alleleId: '=?', // If allele workflow
        analysisId: '=?', // If analysis workflow
        genepanelName: '=?',
        genepanelVersion: '=?',
        // reload: '&?',
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
            start: {
                text: 'Start'
            },
            review: {
                text: 'Start review'
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
        let type_id;
        if ('analysisId' in this) {
            type_id = ['analysis', this.analysisId];
        }
        else if ('alleleId' in this) {
            type_id = ['allele', this.alleleId];
        }
        else {
            throw Error("Neither alleleId nor analysisId is defined.")
        }
        return type_id;
    }

    _callReload() {
        let [type, id] = this.getTypeAndId()
        this.interpretationService.load(type, id, this.genepanelName, this.genepanelVersion)
        // // Let parent know that it should reload data
        // if (this.reload) {
        //     this.reload();
        // }
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
        let selected_interpretation = this.interpretationService.getSelectedInterpretation()
        // Reassign/save mode
        if (selected_interpretation && selected_interpretation.status === 'Ongoing') {
            if (selected_interpretation.user.id !== this.user.getCurrentUserId()) {
                this.interpretationOverrideModal.show().then(result => {
                    if (result) {
                        this.workflowService.override(type, id).then(() => this._callReload());
                    }
                });
            }
            else {
                this.workflowService.save(type, id, selected_interpretation).then(() => {
                    this.interpretationUpdateInProgress = false;
                }).catch(() => {
                    this.toastr.error("Something went wrong while saving your work. To avoid losing it, please don't close this window and contact support.");
                });
            }
        }
        else {
            let interpretations = this.interpretationService.getAllInterpretations()
            // Call reopen if applicable
            if (interpretations.length && interpretations.every(i => i.status === 'Done')) {
                this.workflowService.reopen(type, id).then(() => {
                    if (this.startWhenReopen) {
                        this.workflowService.start(type, id, this.genepanelName, this.genepanelVersion).then(() => this._callReload());
                    }
                    else {
                        this._callReload();
                    }
                });
            }
            // Else start interpretation
            else {
                this.workflowService.start(type, id, this.genepanelName, this.genepanelVersion).then(() => this._callReload());
            }
        }
    }

    clickFinishBtn() {
        let [type, id] = this.getTypeAndId();
            // TODO: Redirect user
        this.workflowService.confirmCompleteFinalize(type, id, this.interpretationService.getSelectedInterpretation(), this.alleles, this.config).then((redirect) => {
            if (redirect) {
                this.location.path('/overview');
            }
        });
    }

    showFinishBtn() {
        let selected_interpretation = this.interpretationService.getSelectedInterpretation()
        if (selected_interpretation && selected_interpretation.status === 'Ongoing') {
                return selected_interpretation.user.id === this.user.getCurrentUserId();
        }
        return false;
    }

    _getSaveStatus() {
        let interpretations = this.interpretationService.getAllInterpretations()
        if (!interpretations) {
            return 'start';
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
            return interpretations.length > 1 ? 'review' : 'start'
        }

        if (interpretations.length &&
            interpretations.every(i => i.status === 'Done')) {
            return 'reopen';
        }

        return 'start';
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
        if (['start', 'review'].includes(this._getSaveStatus())) {
            classes.push('green');
        }
        else if (['override'].includes(this._getSaveStatus())) {
            classes.push('red');
        }
        else {
            if (this.selectedInterpretation &&
                this.selectedInterpretation.dirty) {
                classes.push('pink');
            }
            else {
                classes.push('blue');
            }
        }
        return classes;
    }


}
