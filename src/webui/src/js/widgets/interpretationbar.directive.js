/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {ACMGHelper} from '../model/acmghelper';
@Directive({
    selector: 'interpretationbar',
    scope: {
        analysis: '=?',
        allele: '=',
        components: '=',
        selectedComponent: '=',
        onComponentChange: '&?',
        readOnly: '='
    },
    templateUrl: 'ngtmpl/interpretationbar.ngtmpl.html'
})
@Inject('$scope',
    'Interpretation',
    'AddExcludedAllelesModal',
    'clipboard',
    'toastr',
    'Config',
    '$filter'
    )
export class Interpretationbar {

    constructor($scope,
                Interpretation,
                AddExcludedAllelesModal,
                clipboard,
                toastr,
                Config,
                $filter) {
        this.interpretationService = Interpretation;
        this.addExcludedAllelesModal = AddExcludedAllelesModal;
        this.clipboard = clipboard;
        this.toastr = toastr;
        this.config = Config.getConfig()
        this.filter = $filter;

        this.pathogenicPopoverToggle = {
          buttons: [ 'Pathogenic', 'Benign' ],
          model: 'Pathogenic'
        };

        this.popover = {
            templateUrl: 'ngtmpl/acmgSelectionPopover.ngtmpl.html'
        };

        this.setACMGCandidates();
    }

    getInterpretationType() {
        return this.interpretationService.type;
    }

    getSelectedInterpretation() {
        return this.interpretationService.getSelected()
    }

    /**
     * Returns allelestate object for the provided allele.
     * If the allelestate doesn't exist, create it first.
     * @param  {Allele} allele
     * @return {Object} allele state for given allele
     */
    getAlleleState(allele) {
        let selectedInterpretation = this.getSelectedInterpretation();
        if (!('allele' in selectedInterpretation.state)) {
            selectedInterpretation.state.allele = {};
        }
        if (!(allele.id in selectedInterpretation.state.allele)) {
            let allele_state = {
                allele_id: allele.id,
            };
            selectedInterpretation.state.allele[allele.id] = allele_state;
        }
        return selectedInterpretation.state.allele[allele.id];
    }

    getAlleleUserState(allele) {
        let selectedInterpretation = this.getSelectedInterpretation();
        if (!('allele' in selectedInterpretation.user_state)) {
            selectedInterpretation.user_state.allele = {};
        }
        if (!(allele.id in selectedInterpretation.user_state.allele)) {
            let allele_state = {
                allele_id: allele.id,
                showExcludedReferences: false,
            };
            selectedInterpretation.user_state.allele[allele.id] = allele_state;
        }
        return selectedInterpretation.user_state.allele[allele.id];
    }



    // Controls
    collapseAll() {
        let section_states = Object.values(this.getAlleleUserState(this.allele).sections);
        let current_collapsed = section_states.map(s => s.collapsed);
        let some_collapsed = current_collapsed.some(c => c);
        for (let section_state of section_states) {
            section_state.collapsed = !some_collapsed;
        }
    }

    getExcludedAlleleCount() {
        if (this.getSelectedInterpretation()) {
            return Object.values(this.getSelectedInterpretation().excluded_allele_ids)
                .map(excluded_group => excluded_group.length)
                .reduce((total_length, length) => total_length + length);
        }
    }

    loadAlleles() {
        this.interpretationService.loadAlleles(true) // Reload view
    }

    getAlleles() {
        return this.interpretationService.getAlleles()
    }

    /**
     * Popups a dialog for adding excluded alleles
     */
    modalAddExcludedAlleles() {
        if (this.getSelectedInterpretation().state.manuallyAddedAlleles === undefined) {
            this.getSelectedInterpretation().state.manuallyAddedAlleles = [];
        }
        this.addExcludedAllelesModal.show(
            this.getSelectedInterpretation().excluded_allele_ids,
            this.getSelectedInterpretation().state.manuallyAddedAlleles,
            this.getAnalysis().samples[0].id, // FIXME: Support multiple samples
            this.getSelectedInterpretation().genepanel_name,
            this.getSelectedInterpretation().genepanel_version,
            this.readOnly
        ).then(added => {
            if (this.isInterpretationOngoing()) { // noop if analysis is finalized
                // Uses the result of modal as it's more excplicit than mutating the inputs to the show method
                this.getSelectedInterpretation().state.manuallyAddedAlleles = added;
                this.loadAlleles();
            }
        }).catch(() => {
            this.loadAlleles();  // Also update on modal dismissal
        });
    }

    copyAllAlamut() {
        this.clipboard.copyText(
            this.getAlleles().map(a => a.formatAlamut() + '\n').join('')
        );
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }

    copySingleAlamut() {
        this.clipboard.copyText(this.allele.formatAlamut());
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }

    showHistory() {
        return !this.isInterpretationOngoing() && this.getInterpretationHistory().length;
    }

    getInterpretationHistory() {
        return this.interpretationService.getHistory()
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

    getAllInterpretations() {
        return this.interpretationService.getAll()
    }

    isInterpretationOngoing() {
        return this.interpretationService.isOngoing()
    }

    getGenepanel() {
        return this.interpretationService.getGenepanel()
    }

    getAnalysis() {
        return this.interpretationService.getAnalysis()
    }


    ///////////////
    /// ACMG popover
    ///////////////

    /**
     * Create list of ACMG code candidates for showing
     * in popover. Sorts the codes into array of arrays,
     * one array for each group.
     */
    setACMGCandidates() {
        this.acmgCandidates = {};

        let candidates = Object.keys(this.config.acmg.explanation).filter(code => !code.startsWith('REQ'));

        for (let t of ['benign', 'pathogenic']) {
            this.acmgCandidates[t] = [];

            // Map codes to group (benign/pathogenic)
            for (let c of candidates) {
                if (this.config.acmg.codes[t].some(e => c.startsWith(e))) {
                    if (!this.acmgCandidates[t].includes(c)) {
                        this.acmgCandidates[t].push(c);
                    }
                }
            }

            // Sort the codes
            this.acmgCandidates[t].sort((a, b) => {
                // Find the difference in index between the codes
                let a_idx = this.config.acmg.codes[t].findIndex(elem => a.startsWith(elem));
                let b_idx = this.config.acmg.codes[t].findIndex(elem => b.startsWith(elem));

                // If same prefix, sort on text itself
                if (a_idx === b_idx) {
                    return a.localeCompare(b);
                }
                if (t === "benign") {
                    return b_idx - a_idx;
                } else {
                    return a_idx - b_idx;
                }
            });
            // Pull out any codes with an 'x' in them, and place them next after their parent code
            // This bugs out for a few codes that don't have parents, but is good enough for now
            let x_codes = [];
            x_codes = this.acmgCandidates[t].filter( (e) => { if(e.includes('x')) { return true; } } );
            x_codes.forEach( (e) => { this.acmgCandidates[t].splice(this.acmgCandidates[t].indexOf(e),1) } );
            x_codes.forEach( (e) => {
              this.acmgCandidates[t].splice(
                (this.acmgCandidates[t].indexOf(e.split('x')[1])+1),
                0, e
              )
            })
        }
    }

    getExplanationForCode(code) {
        return this.config.acmg.explanation[code];
    }

    getACMGpopoverClass(code) {
      let acmgclass = this.getACMGClass(code);
      return code.includes('x') ? `indented ${acmgclass}` : acmgclass;
    }

    /**
     * Lets user include a code not provided by backend.
     * @param {String} code Code to add
     */
    addStagedACMGCode() {
        if (this.staged_code) {
            this.includeACMG(this.staged_code);
        }
        this.staged_code = null;
    }

    /**
     * "Stages" an ACMG code in the popover, for editing before adding it.
     * @param {String} code Code to add
     */
    stageACMGCode(code) {
        let existing_comment = this.staged_code ? this.staged_code.comment : '';
        this.staged_code = ACMGHelper.userCodeToObj(code, existing_comment);
    }

    getACMGClass(code) {
        return code.substring(0, 2).toLowerCase();
    }

    includeACMG(code) {
        ACMGHelper.includeACMG(code, this.allele, this.getAlleleState(this.allele));
    }

}
