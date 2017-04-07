/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

@Directive({
    selector: 'allele-info-vardb',
    scope: {
        allele: '=',
        alleleState: '=',
        readOnly: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoVardb.ngtmpl.html'
})
@Inject('Config', 'AlleleAssessmentHistoryModal')
export class AlleleInfoVardb {

    constructor(Config, AlleleAssessmentHistoryModal) {
        this.config = Config.getConfig();
        this.alleleAssessmentHistoryModal = AlleleAssessmentHistoryModal;
    }

    hasContent() {
        return Boolean(this.allele.allele_assessment);
    }

    showHistory() {
        this.alleleAssessmentHistoryModal.show(this.allele.id);
    }
}
