import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default (hgncId) => {
    return Compute(
        hgncId,
        state`views.workflows.interpretation.data.genepanel`,
        (hgncId, genepanel) => {
            if (!hgncId || !genepanel) {
                return
            }
            const existing = genepanel.geneassessments.find((ga) => ga.gene_id === hgncId)
            if (existing) {
                return existing
            } else {
                // Return empty model to have something to start from
                return {
                    gene_id: hgncId,
                    evaluation: {
                        comment: ''
                    }
                }
            }
        }
    )
}
