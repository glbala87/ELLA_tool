/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'interpretation-bar',
    scope: {
        'interpretation': '=',
        'excludedAlleles': '=',
        'includedAlleles': '='
    },
    templateUrl: 'ngtmpl/interpretationbar.ngtmpl.html'
})
@Inject('AddExcludedAllelesModal', 'Interpretation', 'Config', 'User')
export class InterpretationBarController {
    constructor(AddExcludedAllelesModal, interpretationService, Config, User) {
        this.addExcludedAllelesModal = AddExcludedAllelesModal;
        this.interpretationService = interpretationService;
        this.config = Config;
        this.user = User;
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
    }

    updateInterpretation() {
        this.interpretationUpdateInProgress = true;
        this.interpretationService.save(this.interpretation).then(() => {
            this.interpretationUpdateInProgress = false;
        });
        // FIXME: Handle exception case as it can mean another user started
        // the interpretation right before our user.
    }

    completeInterpretation() {
        this.interpretationService.confirmCompleteFinalize(this.interpretation);
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
                classes.push('faded-green');
            }
            else {
                if (this.interpretation.dirty) {
                    classes.push('faded-red');
                }
                else {
                    classes.push('faded-blue');
                }
            }
        }
        return classes;
    }

    /**
     * Popups a dialog for adding excluded alleles
     */
    modalAddExcludedAlleles() {
        if (this.includedAlleles === undefined) {
            this.includedAlleles = [];
        }
        this.addExcludedAllelesModal.show(this.excludedAlleles, this.includedAlleles).then(added => {
            this.includedAlleles = added;
        });
    }
}
