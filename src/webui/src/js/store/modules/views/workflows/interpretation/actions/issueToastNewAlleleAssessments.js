export default function issueToastNewAlleleAssessments({ props, state, toast }) {
    const { updatedAlleleAssessmentAlleleIds } = props

    const workflowType = state.get('views.workflows.type')
    const workflowId = state.get('views.workflows.id')

    if (updatedAlleleAssessmentAlleleIds.length) {
        const loadedAlleles = updatedAlleleAssessmentAlleleIds.map((alleleId) =>
            state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
        )

        // Check that the allele assessments were not made as part of this workflow
        // (if so, giving a warning is useless)
        let updatedAlleleAssessmentAlleles = []
        if (workflowType === 'allele') {
            // If there's a change while in allele workflow,
            // the change must have happened in an analysis workflow
            updatedAlleleAssessmentAlleles = loadedAlleles.filter(
                (a) => a.allele_assessment.analysis_id !== null
            )
        } else {
            updatedAlleleAssessmentAlleles = loadedAlleles.filter(
                (a) => a.allele_assessment.analysis_id !== workflowId
            )
        }
        if (updatedAlleleAssessmentAlleles.length) {
            const formattedAlleles = updatedAlleleAssessmentAlleles.map((a) => {
                return 'display' in a.formatted ? a.formatted.display : a.formatted.hgvsg
            })

            let text = `A new evaluation was loaded for: ${formattedAlleles.join(', ')}`
            toast.show('info', text, null, true)
        }
    }
}
