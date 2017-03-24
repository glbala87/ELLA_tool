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
        this.toastr = toastr;

        this.show_req = true;
        this.req_groups = []; // Updated by setREQCodes()

        $scope.$watch(() => this.allele.acmg, () => {
            if (this.allele.acmg) {
                ACMGHelper.populateSuggestedACMG(this.allele, this.alleleState);
                this.setREQCodes();
            }
        }, true); // Deep watch the ACMG part


        ACMGHelper.populateSuggestedACMG(this.allele, this.alleleState);
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

    isIncludable(code) {
        return ACMGHelper.isIncludable(code);
    }

    addACMGCodeFromString(code) {
        let code_obj = ACMGHelper.userCodeToObj(code);
        this.includeACMG(code_obj);
    }

    includeACMG(code) {
        ACMGHelper.includeACMG(code, this.allele, this.alleleState);
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
