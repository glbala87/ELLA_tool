/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

@Directive({
    selector: 'workflow-buttons',
    scope: {
        currentInterpretation: '=',
        historyInterpretations: '=',
        alleleId: '=?', // If allele workflow
        analysisId: '=?', // If analysis workflow
        canFinish: '=?',
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
            'save': {
                class: '',
                text: 'Save'
            },
            'start': {
                class: '',
                text: 'Start analysis'
            }
        };

        if (!('alleleId' in this) && !('analysisId' in this)) {
            throw Error("Neither alleleId nor analysisId is defined.")
        }

    }

    /**
     * Checks whether user is allowed to finish the analysis.
     * Criteria is that every allele must have an alleleassessment _with a classification_.
     * @return {bool}
     */
    /*canFinish() {
        if (!this.alleles.length) {
            return true;
        }

        return this.alleles.every(a => {
            let allele_state = this.interpretation.state.allele.find(s => s.allele_id === a.id);
            return Boolean(AlleleStateHelper.getClassification(a, allele_state));
        });
    }*/

    _callReload() {
        // Let parent know that it should reload data
        if (this.reload) {
            this.reload();
        }
    }

    /**
     * Handles start/save button logic.
     * Start logic:
     * If no currentInterpretation, but historyInterpretations > 1, we need to reopen workflow
     * using the reopen actions. If not, just call start action.
     *
     * Save logic:
     * Just call save on workflowService.
     * Only works if there is a currentInterpretation with status 'Ongoing'.
     *
     */
    clickStartSaveBtn() {
        let type = '';
        let id = -1;
        if ('analysisId' in this) {
            type = 'analysis';
            id = this.analysisId;
        }
        else if ('alleleId' in this) {
            type = 'allele';
            id = this.alleleId;
        }
        // Save mode
        if (this.currentInterpretation && this.currentInterpretation.status === 'Ongoing') {
            this.workflowService.save(type, id, this.currentInterpretation).then(() => {
                this.interpretationUpdateInProgress = false;
                this._callReload();
            }).catch(() => {
                this.toastr.error("Something went wrong while saving your work. To avoid losing it, please don't close this window and contact support.");
            });
        }
        else {
            // Call reopen if applicable
            if (!this.currentInterpretation && this.historyInterpretations.length) {
                this.workflowService.reopen(type, id).then(() => this._callReload());
            }
            // Else start interpretation
            else {
                this.workflowService.start(type, id).then(() => this._callReload());
            }
        }
    }

    _getSaveStatus() {
        if (this.interpretation) {
            return this.interpretation.status === 'Not started' ? 'start' : 'save';
        }
        return 'start';
    }

    getSaveBtnText() {
        return this.saveButtonOptions[this._getSaveStatus()].text;
    }

    getSaveBtnClass() {
        let classes = [];
        if (this.interpretation) {
            if (this._getSaveStatus() === 'start') {
                classes.push('green');
            }
            else {
                if (this.interpretation.dirty) {
                    classes.push('pink');
                }
                else {
                    classes.push('blue');
                }
            }
        }
        return classes;
    }


}
