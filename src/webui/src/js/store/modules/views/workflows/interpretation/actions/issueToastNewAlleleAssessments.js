export default function issueToastNewAlleleAssessments({ props, state, toast }) {
    const { newAlleleAssessmentAlleleIds } = props

    if (newAlleleAssessmentAlleleIds.length) {
        const loadedAlleles = newAlleleAssessmentAlleleIds.map((alleleId) =>
            state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
        )

        const formattedAlleles = loadedAlleles.map((a) => {
            return 'display' in a.formatted ? a.formatted.display : a.formatted.hgvsg
        })

        let text = ''
        if (loadedAlleles.length > 1) {
            text = `New evaluations were loaded for variants: ${formattedAlleles.join(', ')}`
        } else {
            text = `A new evaluation was loaded for variant: ${formattedAlleles[0]}`
        }
        toast.show('info', text, null, true)
    }
}
