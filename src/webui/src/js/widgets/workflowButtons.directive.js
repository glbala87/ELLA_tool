/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

@Directive({
    selector: 'workflow-buttons',
    scope: {
        selectedInterpretation: '=',
        interpretations: '=',
        alleles: '=',
        alleleId: '=?', // If allele workflow
        analysisId: '=?', // If analysis workflow
        reload: '&?'
    },
    templateUrl: 'ngtmpl/workflowButtons.ngtmpl.html'
})
@Inject('Workflow', 'Config', 'User', 'toastr')
export class WorkflowButtonsController {
    constructor(Workflow, Config, User, toastr) {
        this.workflowService = Workflow;
        this.config = Config;
        this.user = User;
        this.toastr = toastr;
        this.interpretationUpdateInProgress = false;

        this.saveButtonOptions = {
            save: {
                text: 'Save'
            },
            start: {
                text: 'Start analysis'
            },
            review: {
                text: 'Start review'
            },
            reopen: {
                text: 'Reopen analysis'
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
        // Let parent know that it should reload data
        if (this.reload) {
            this.reload();
        }
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
        // Save mode
        if (this.selectedInterpretation && this.selectedInterpretation.status === 'Ongoing') {
            this.workflowService.save(type, id, this.selectedInterpretation).then(() => {
                this.interpretationUpdateInProgress = false;
            }).catch(() => {
                this.toastr.error("Something went wrong while saving your work. To avoid losing it, please don't close this window and contact support.");
            });
        }
        else {
            // Call reopen if applicable
            if (this.interpretations.every(i => i.status === 'Done')) {
                this.workflowService.reopen(type, id).then(() => this._callReload());
            }
            // Else start interpretation
            else {
                this.workflowService.start(type, id).then(() => this._callReload());
            }
        }
    }

    clickFinishBtn() {
        let [type, id] = this.getTypeAndId();
            // TODO: Redirect user
        this.workflowService.confirmCompleteFinalize(type, id, this.selectedInterpretation, this.alleles).then(() => {this._callReload()});
    }

    isInterpretationOngoing() {
        if (this.selectedInterpretation) {
            return this.selectedInterpretation.status === 'Ongoing';
        }
        return false;
    }

    _getSaveStatus() {

        if (this.interpretations.find(i => i.status === 'Ongoing')) {
            return 'save';
        }

        let not_started = this.interpretations.find(i => i.status === 'Not started');
        if (not_started) {
            return this.interpretations.length > 1 ? 'review' : 'start'
        }

        if (this.interpretations.every(i => i.status === 'Done')) {
            return 'reopen';
        }

        return 'start';
    }

    getSaveBtnText() {
        return this.saveButtonOptions[this._getSaveStatus()].text;
    }

    getSaveBtnClass() {
        let classes = [];
        if (this._getSaveStatus() === 'start') {
            classes.push('green');
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
