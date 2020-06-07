export default function clearSupercededGeneAssessments({ state }) {
    // Checks userState whether we have any work in progress gene assessments
    // and updates (clears) them if they are superceded.
    const geneAssessments = state.get(
        'views.workflows.interpretation.data.genepanel.geneassessments'
    )
    const userGeneAssessments = state.get('views.workflows.interpretation.userState.geneassessment')
    if (!userGeneAssessments) {
        return
    }
    for (let ga of geneAssessments) {
        if (ga.gene_id in userGeneAssessments) {
            if (ga.id != userGeneAssessments[ga.gene_id].id) {
                state.unset(`views.workflows.interpretation.userState.geneassessment.${ga.gene_id}`)
            }
        }
    }
}
