import { deepCopy } from '../../../../../util'

export default function copyExistingAlleleReports({ state }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')

    for (let [aId, allele] of Object.entries(alleles)) {
        if (!allele.allele_report) {
            continue
        }
        const alleleReport = state.get(
            `views.workflows.interpretation.state.allele.${aId}.allelereport`
        )

        if (!alleleReport.copiedFromId || allele.allele_report.id > alleleReport.copiedFromId) {
            alleleReport.evaluation = deepCopy(allele.allele_report.evaluation)
            alleleReport.copiedFromId = allele.allele_report.id
        }
        state.set(`views.workflows.interpretation.state.allele.${aId}.allelereport`, alleleReport)
    }
}
