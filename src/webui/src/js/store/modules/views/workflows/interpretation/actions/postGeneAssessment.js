import getGeneAssessment from '../computed/getGeneAssessment'

export default function postGeneAssessment({ state, props, http, path, resolve }) {
    const { geneAssessment } = props

    const existingGeneAssessment = resolve.value(getGeneAssessment(geneAssessment.gene_id))
    const { name, version } = state.get('views.workflows.selectedGenepanel')
    const analysisId = state.get('views.workflows.data.analysis.id')

    const payload = {
        gene_id: geneAssessment.gene_id,
        evaluation: geneAssessment.evaluation,
        genepanel_name: name,
        genepanel_version: version
    }
    if (analysisId) {
        payload.analysis_id = analysisId
    }
    if (existingGeneAssessment) {
        payload.presented_geneassessment_id = existingGeneAssessment.id
    }
    return http
        .post(`geneassessments/`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}
