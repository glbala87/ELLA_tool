import angular from 'angular'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'

export default function(alleleId) {
    return Compute(
        getAlleleState(alleleId),
        state`views.workflows.interpretation.data.alleles.${alleleId}`,
        (alleleState, allele) => {
            if (!alleleState || !allele) {
                return false
            }
            // Whether allelereport is considered updated, so that user must "Submit report" or
            // discard report changes

            // There are three cases:
            // - No existing assessment/report:
            //    return false, initial allele report is created
            //    as part of finalize allele (i.e. along with an alleleassessment)
            // - Existing alleleassessment/report, evaluation is the same:
            //    return false, no changes
            // - Existing alleleassessment/report, evaluation is different:
            //    return true, something has changed
            return Boolean(
                allele.allele_report &&
                    alleleState.allelereport &&
                    angular.toJson(alleleState.allelereport.evaluation) !=
                        angular.toJson(allele.allele_report.evaluation)
            )
        }
    )
}
