import { Compute } from 'cerebral';
import { state } from 'cerebral/tags';
import getClassification from '../interpretation/computed/getClassification';

export default function(inverse = false, alleles) {
    return Compute(
        alleles,
        state`views.workflows.interpretation.selected`,
        (alleles, interpretation, get) => {
            return alleles.filter((allele) => {
                const hasClassification = get(
                    getClassification(state`views.workflows.data.alleles.${allele.id}`)
                ).hasClassification
                return inverse ? !hasClassification : hasClassification
            })
        }
    )
}
