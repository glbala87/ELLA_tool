/* jshint esnext: true */

import {AlleleStateHelper} from './allelestatehelper';
import {deepCopy, UUID} from '../util';

/**
 * Handles ACMG code logic and how they interact with alleleState.
 *
 * Logic is briefly like this:
 *  - Suggested codes (from backend) is located in allele.acmg
 *  - Suggested codes are copied into 'suggested' in alleleassessment in alleleState (for snapshotting)
 *  - If user includes an ACMG code into their evaluation, we make a copy of the code under the 'included' key
 *  - Any user added codes are directly added under 'included' key
 * @export
 * @class ACMGHelper
 */
export class ACMGHelper {

    /**
     * (Re)creates suggested codes (from allele.acmg) into the 'suggested' section
     * of the alleleassessment.evaluation, if they aren't created already.
     * This is done in order to log what the user saw as suggested codes.
     */
    static populateSuggestedACMG(allele, allele_state) {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(allele, allele_state)) {
            return;
        }

        allele_state.alleleassessment.evaluation.acmg.suggested = [];
        if (allele.acmg) {
            for (let c of allele.acmg.codes) {
                // Filter out the ones already included.
                if (this.isACMGInIncluded(c, allele, allele_state)) {
                    continue;
                }
                allele_state.alleleassessment.evaluation.acmg.suggested.push(this.remoteCodeToObj(c));
            }
        }
    }

    static userCodeToObj(code, comment='') {
        return {
            code: code,
            source: 'user',
            match: null,
            op: null,
            comment: comment,
            uuid: UUID()
        };
    }

    /**
     * Converts a ACMG code from backend into what we keep in state.
     * By default, there's no comment field. That is added on demand in includeACMG().
     * @param  {Object} code ACMG code as part of allele from backend
     * @return {Object}      Data to keep in state
     */
    static remoteCodeToObj(code) {
        return {
            code: code.code,
            source: code.source,
            op: code.op || null,
            match: code.match || null
        };
    }

    /**
     * Method for comparing two acmg state objects.
     * If they have UUIDs, compare by them.
     * If not we use code, source and match as keys.
     */
    static compareACMGObjs(a1, a2) {
        if (a1.uuid && a2.uuid) {
            return a1.uuid === a2.uuid;
        }
        return a1.code === a2.code &&
               a1.source === a2.source &&
               (a1.match === null || a2.match === null ||
                a1.match.every((e, idx) => a2.match[idx] === e)); // .match is array
    }

    static isIncludable(code) {
        return !code.startsWith('REQ');
    }

    /**
     * Copies the input ACMG object (should be from the 'included' section of the
     * alleleassessment in the alleleState) into 'included' section of said state.
     */
    static includeACMG(code, allele, allele_state) {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(allele, allele_state)) {
            return;
        }
        let copy_code = deepCopy(code);
        if (!copy_code.comment) {
            copy_code.comment = ''; // Add comment field, included codes have comments
        }
        copy_code.uuid = UUID();
        allele_state.alleleassessment.evaluation.acmg.included.push(copy_code);
    }

    static excludeACMG(code, allele, allele_state) {
        // Only update data if we're modifying the allele state,
        // we don't want to overwrite anything in any existing allele assessment
        if (AlleleStateHelper.isAlleleAssessmentReused(allele, allele_state)) {
            return;
        }

        // Remove first match from included array (only first match, since duplicates are allowed)
        let idx = allele_state.alleleassessment.evaluation.acmg.included.findIndex(e => {
            return this.compareACMGObjs(code, e);
        });
        if (idx < 0) {
            throw Error("Couldn't find matching code. This shouldn't happen.")
        }
        let included = allele_state.alleleassessment.evaluation.acmg.included.splice(idx, 1)[0];
    }

    /**
     * Checks whether ACMG code is included in alleleassessment.
     * @return {Boolean} True if it's included
     */
    static isACMGInIncluded(code, allele, allele_state) {
        let alleleassessment = AlleleStateHelper.getAlleleAssessment(
            allele,
            allele_state
        );

        if (!('acmg' in alleleassessment.evaluation)) {
            return false;
        }
        return alleleassessment.evaluation.acmg.included.find(elem =>  {
            return this.compareACMGObjs(elem, code);
        }) !== undefined;
    }

    static isACMGInSuggested(code, allele, allele_state) {
        let alleleassessment = AlleleStateHelper.getAlleleAssessment(
            allele,
            allele_state
        );
        return alleleassessment.evaluation.acmg.suggested.find(elem =>  {
            return this.compareACMGObjs(elem, code);
        }) !== undefined;
    }

    /**
     * Returns the base ACMG code, without strength applier.
     *
     * @param {String} code_str
     */
    static getCodeBase(code_str) {
        if (code_str.includes('x')) {
            return code_str.split('x', 2)[1];
        }
        return code_str;
    }

    static _upgradeDowngradeCode(code_str, config, upgrade=true) {
        let code_strength, base;
        if (code_str.includes('x')) {
            [code_strength, base] = code_str.split('x', 2);
        }

        // If code is benign, upgrading the code should mean 'more benign' and vice versa
        if (this._extractCodeType(code_str) === "benign") {
            upgrade = !upgrade;
        }

        for (let strengths of Object.values(config.acmg.codes)) {
            // If strength is given (i.e. the code is not already upgraded/downgraded)
            // we need to find the strength of the base.
            if (code_strength === undefined) {
                base = code_str;
                for (let s of strengths) {
                    if (code_str.startsWith(s)) {
                        code_strength = s;
                    }
                }
            }

            let strength_idx = strengths.indexOf(code_strength);
            if (strength_idx < 0) {  // If strength not part of set, try next one
                continue;
            }

            // Check whether we can upgrade code, or if it would overflow
            let overflow = upgrade ? strength_idx == 0 : strength_idx >= strengths.length-1;
            if (!overflow) {
                let new_strength = upgrade ? strengths[strength_idx-1] : strengths[strength_idx+1];
                // If new strength is same as base we just return base
                if (base.startsWith(new_strength)) {
                    return base;
                }
                return `${new_strength}x${base}`;
            }
            // If overflowing, return input
            return code_str;
        }
        return code_str;
    }

    static upgradeCodeObj(code, config) {
        code.code = this._upgradeDowngradeCode(code.code, config, true);
        return code;
    }
    
    static canUpgradeCodeObj(code, config) {
        return code.code !== this._upgradeDowngradeCode(code.code, config, true);
    }

    static downgradeCodeObj(code, config) {
        code.code = this._upgradeDowngradeCode(code.code, config, false);
        return code;
    }
    
    static canDowngradeCodeObj(code, config) {
        return code.code !== this._upgradeDowngradeCode(code.code, config, false);
    }
 
    static _extractCodeType(code_str) {
        let base = this.getCodeBase(code_str);
        if (base.startsWith("B")) {
            return "benign"
        } else {
            return "pathogenic"
        }
    }
}
