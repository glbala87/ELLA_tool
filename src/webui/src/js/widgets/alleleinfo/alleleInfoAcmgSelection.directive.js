/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-acmg-selection',
    scope: {
        allele: '=',
        alleleState: '='
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
        this.popover = {
            templateUrl: 'ngtmpl/acmgSelectionPopover.ngtmpl.html'
        };

        this.show_req = true;
        this.req_groups = []; // Updated by setREQCodes()

        $scope.$watch(() => this.allele.acmg, () => {
            if (this.allele.acmg) {
                this.setupSuggestedACMG();
                this.setREQCodes();
            }
        }, true); // Deep watch the ACMG part

        // Update suggested classification whenever user changes
        // included ACMG codes
        $scope.$watchCollection(
            () => this.alleleState.alleleassessment.evaluation.acmg.included,
            () => this.updateSuggestedClassification()
        );
        this.setupStructure();
        this.setupSuggestedACMG();
        this.setACMGCandidates();
    }

    getSuggestedClassification() {
        if (this.alleleState.alleleassessment.evaluation.acmg.suggested_classification !== null) {
            return this.alleleState.alleleassessment.evaluation.acmg.suggested_classification;
        } else {
            return "none yet";
        }
    }

    updateSuggestedClassification() {
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
        return !code.startsWith('REQ');
    }

    /**
     * Lets user include a code not provided by backend.
     * @param {String} code Code to add
     */
    addACMGCode(code) {
        let user_code = {
            code: code,
            source: 'user',
            match: null,
            op: null,
            comment: ''
        }
        this.includeACMG(user_code);
    }

    getACMGClass(code) {
        return code.substring(0, 2).toLowerCase();
    }

    setupStructure() {
        if (!('alleleassessment' in this.alleleState)) {
            this.alleleState.alleleassessment = {};
        }
        if (!('evaluation' in this.alleleState.alleleassessment)) {
            this.alleleState.alleleassessment.evaluation = {};
        }
        if (!('acmg' in this.alleleState.alleleassessment.evaluation)) {
            this.alleleState.alleleassessment.evaluation.acmg = {};
        }
        if (!('suggested' in this.alleleState.alleleassessment.evaluation.acmg)) {
            this.alleleState.alleleassessment.evaluation.acmg.suggested = [];
        }
        if (!('included' in this.alleleState.alleleassessment.evaluation.acmg)) {
            this.alleleState.alleleassessment.evaluation.acmg.included = [];
        }
    }

    /**
     * (Re)creates suggested codes into the 'suggested' section
     * of the alleleassessment.evaluation, if they aren't created already.
     * This is done in order to log what the user saw as suggested codes.
     */
    setupSuggestedACMG() {
        this.alleleState.alleleassessment.evaluation.acmg.suggested = [];
        if (this.allele.acmg) {
            for (let c of this.allele.acmg.codes) {
                // Filter out the ones already included.
                if (this.isACMGInIncluded(c)) {
                    continue;
                }
                this.alleleState.alleleassessment.evaluation.acmg.suggested.push(this._codeToStateObj(c));
            }
        }
    }

    /**
     * Method for comparing two acmg state objects.
     * We use code, source and match as keys.
     */
    _compareACMG(a1, a2) {
        return a1.code === a2.code &&
               a1.source === a2.source &&
               (a1.match === null || a2.match === null ||
                a1.match.every((e, idx) => a2.match[idx] === e) // match is array
               )
    }

    /**
     * Converts a ACMG code from backend into
     * what we keep in state.
     * @param  {Object} code ACMG code as part of allele from backend
     * @return {Object}      Data to keep in state
     */
    _codeToStateObj(code) {
        return {
            code: code.code,
            source: code.source,
            op: code.op || null,
            match: code.match || null,
            comment: ''
        }
    }

    /**
     * Checks whether ACMG code is included in alleleassessment.

     * @return {Boolean} True if it's included
     */
    isACMGInIncluded(code) {
        return this.alleleState.alleleassessment.evaluation.acmg.included.find(elem =>  {
            return this._compareACMG(elem, code);
        }) !== undefined;
    }

    isACMGInSuggested(code) {
        return this.alleleState.alleleassessment.evaluation.acmg.suggested.find(elem =>  {
            return this._compareACMG(elem, code);
        }) !== undefined;
    }

    /**
     * Copies the input ACMG object (should be from the 'included' section of the
     * alleleassessment in the alleleState) into 'included' section of said state.
     * @param  {[type]} state_acmg Object from 'included' section of state
     */
    includeACMG(code) {
        this.alleleState.alleleassessment.evaluation.acmg.included.push(code);
        // Remove from 'suggested'
        this.alleleState.alleleassessment.evaluation.acmg.suggested = this.alleleState.alleleassessment.evaluation.acmg.suggested.filter(e => {
            return !this._compareACMG(code, e);
        });
    }

    excludeACMG(code) {
        // Remove first match from included array (only first match, since duplicates are allowed)
        let idx = this.alleleState.alleleassessment.evaluation.acmg.included.findIndex(e => {
            return this._compareACMG(code, e);
        });
        if (idx < 0) {
            throw Error("Couldn't find matching code. This shouldn't happen.")
        }
        let included = this.alleleState.alleleassessment.evaluation.acmg.included.splice(idx, 1)[0];


        // Only add back to suggested if not added by user
        if (included.source !== 'user') {
            this.alleleState.alleleassessment.evaluation.acmg.suggested.push(included);
        }
    }

    /**
     * Return groups of REQ codes.
     * @return {Array(Array(Object))} Array of arrays. Same REQ codes are combined into same list.
     */
    setREQCodes() {
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
        return this.alleleState.alleleassessment.evaluation.acmg.suggested.filter(c => !this.isIncludable(c.code)).length;
    }
}
