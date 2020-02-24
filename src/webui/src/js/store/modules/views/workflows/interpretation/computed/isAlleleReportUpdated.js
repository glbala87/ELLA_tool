import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import getAlleleState from './getAlleleState'
import { compareAlleleReport } from '../../../../../common/helpers/workflow'

export default function(alleleId) {
    return Compute(
        getAlleleState(alleleId),
        state`views.workflows.interpretation.data.alleles.${alleleId}`,
        (alleleState, allele) => {
            if (!alleleState || !allele) {
                return false
            }
            return !compareAlleleReport(alleleState, allele)
        }
    )
}
