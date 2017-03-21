/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';
import {ACMGHelper} from '../../model/acmghelper';

@Directive({
    selector: 'allele-info-acmg-selection',
    scope: {
        allele: '=',
        alleleState: '=',
        readOnly: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoAcmgSelection.ngtmpl.html'
})
@Inject('Config',
        'ACMGClassificationResource',
        '$scope',
        'toastr')
export class ACMGSelectionController {

    constructor(Config,
                ACMGClassificationResource,
                $scope,
                toastr) {
        this.config = Config.getConfig();
        this.acmgClassificationResource = ACMGClassificationResource;
        this.toastr = toastr;

        this.pathogenicPopoverToggle = {
          buttons: [ 'Pathogenic', 'Benign' ],
          model: 'Pathogenic'
        };

        this.popover = {
            templateUrl: 'ngtmpl/acmgSelectionPopover.ngtmpl.html'
        };

        this.show_req = true;
        this.req_groups = []; // Updated by setREQCodes()

        $scope.$watch(() => this.allele.acmg, () => {
            if (this.allele.acmg) {
                ACMGHelper.populateSuggestedACMG(this.allele, this.alleleState);
                this.setREQCodes();
            }
        }, true); // Deep watch the ACMG part

        // Update suggested classification whenever user changes
        // included ACMG codes
        $scope.$watchCollection(
            () => this.alleleState.alleleassessment.evaluation.acmg.included,
            () => this.updateSuggestedClassification()
        );
        ACMGHelper.populateSuggestedACMG(this.allele, this.alleleState);
        this.setACMGCandidates();
    }

    isEditable() {
        return !AlleleStateHelper.isAlleleAssessmentReused(
            this.alleleState
        );
    }

    has(type) {
      let codes = type === "suggested" ? this.getAlleleAssessment().evaluation.acmg.suggested : this.getAlleleAssessment().evaluation.acmg.included
      return codes.some((code) => this.isIncludable(code.code))
    }

    getAlleleAssessment() {
        // Call this wrapper as it will dynamically select between
        // the existing alleleassessment (if reused)
        // and the state alleleassessment (if not reused or not existing)
        return AlleleStateHelper.getAlleleAssessment(
            this.allele,
            this.alleleState
        )
    }

    getSuggestedClassification() {
        if (this.getAlleleAssessment().evaluation.acmg.suggested_classification !== null) {
            return this.getAlleleAssessment().evaluation.acmg.suggested_classification;
        } else {
            return "-";
        }
    }

    updateSuggestedClassification() {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(this.allele, this.alleleState)) {
            return;
        }

        // Clear current in case something goes wrong
        // Having no result is better than wrong result
        this.alleleState.alleleassessment.evaluation.acmg.suggested_classification = null;
        let codes = this.alleleState.alleleassessment.evaluation.acmg.included.map(i => i.code);

        if (codes.length) {
            this.acmgClassificationResource.getClassification(codes).then(result => {
                this.alleleState.alleleassessment.evaluation.acmg.suggested_classification = result.class;
            }).catch(() => {
                this.toastr.error("Something went wrong when updating suggested classification.", null, 5000);
            });
        }
    }

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
                return a_idx - b_idx;
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

    isIncludable(code) {
        return ACMGHelper.isIncludable(code);
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

    addACMGCodeFromString(code) {
        let code_obj = ACMGHelper.userCodeToObj(code);
        ACMGHelper.upgradeCodeObj(code_obj, this.config);
        this.includeACMG(code_obj);
    }

    getACMGpopoverClass(code) {
      let acmgclass = this.getACMGClass(code);
      return code.includes('x') ? `indented ${acmgclass}` : acmgclass;
    }

    getACMGClass(code) {
        return code.substring(0, 2).toLowerCase();
    }

    /**
     * Checks whether ACMG code is included in alleleassessment.

     * @return {Boolean} True if it's included
     */
    isACMGInIncluded(code) {
        return ACMGHelper.isACMGInIncluded(code, this.allele, this.alleleState);
    }

    isACMGInSuggested(code) {
        return ACMGHelper.isACMGInSuggested(code, this.allele, this.alleleState);
    }

    /**
     * Copies the input ACMG object (should be from the 'included' section of the
     * alleleassessment in the alleleState) into 'included' section of said state.
     * @param  {[type]} state_acmg Object from 'included' section of state
     */
    includeACMG(code) {
        ACMGHelper.includeACMG(code, this.allele, this.alleleState);
    }

    excludeACMG(code) {
        ACMGHelper.excludeACMG(code, this.allele, this.alleleState);
    }

    /**
     * Return groups of REQ codes.
     * @return {Array(Array(Object))} Array of arrays. Same REQ codes are combined into same list.
     */
    setREQCodes() {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(this.allele, this.alleleState)) {
            return;
        }

        let req_groups = [];
        let reqs = this.alleleState.alleleassessment.evaluation.acmg.suggested.filter(c => !this.isIncludable(c.code));
        for (let req of reqs) {
            let matching_group = req_groups.find(rg => rg.find(r => r.code === req.code));
            if (matching_group) {
                matching_group.push(req);
            }
            else {
                req_groups.push([req]);
            }
        }
        this.req_groups = req_groups;
    }

    getREQCodeCount() {
        return this.getAlleleAssessment().evaluation.acmg.suggested.filter(c => !this.isIncludable(c.code)).length;
    }
}
