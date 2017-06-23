/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-clinvar',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoClinvar.ngtmpl.html'
})
@Inject('Config', '$scope')
export class AlleleInfoClinvar {

    constructor(Config, $scope) {
        this.config = Config.getConfig();
        this.previous = {};
        this.maxstars = new Array(4);

        $scope.$watch(
            () => this.allele,
            () => {
                if (this.hasContent()) {
                    this.revtext = this.allele.annotation.external.CLINVAR["variant_description"];
                    this.revstars = this.config.annotation.clinvar.clinical_significance_status[this.revtext];
                }
            }
        );
    }

    formatClinvar() {
        let result = [];
        if (this.hasContent()) {
            for (let idx=0; idx<this.allele.annotation.external.CLINVAR["items"].length; idx++) {
                let unformatted = this.allele.annotation.external.CLINVAR["items"][idx];

                // Only show SCV-items
                if (!unformatted.rcv.startsWith("SCV")) {
                    continue;
                }

                let formatted = {};

                let sigtext = unformatted.clinical_significance_descr;
                let phenotypetext = unformatted.traitnames;
                let submitter = unformatted.submitter;
                let last_evaluated = unformatted.last_evaluated;

                formatted["submitter"] = submitter === "" ? "Unknown" : submitter;
                formatted["last_evaluated"] = last_evaluated === "" ? "N/A" : last_evaluated;
                formatted["sigtext"] = sigtext === '' ? "No classification" : sigtext;
                formatted["phenotypetext"] = phenotypetext === '' ? "not specified" : phenotypetext;

                result.push(formatted);
            }
        }
        return result;
    }

    hasContent() {
        return 'CLINVAR' in this.allele.annotation.external;
    }

    idempoClinvar() {
        // Force JSON-representation to be the equal-check
        let cur = this.formatClinvar();
        if (angular.toJson(this.previous) != angular.toJson(cur)) {
            this.previous = cur;
        }
        return this.previous;
    }

    sort(item) {
        // Sort by clinical signifiance, then date
        let sortOrder = ["benign", "likely benign", "uncertain significance", "likely pathogenic", "pathogenic"];
        let sortVal = ""+sortOrder.indexOf(item.sigtext.toLowerCase())
        sortVal += item.last_evaluated.slice(6) // Year
        sortVal += item.last_evaluated.slice(3,5) // Month
        sortVal += item.last_evaluated.slice(0,2) // Day

        return -parseInt(sortVal);
    }
}
