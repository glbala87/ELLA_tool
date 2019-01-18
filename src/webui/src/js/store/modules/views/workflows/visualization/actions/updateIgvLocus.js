export default function updateIgvLocus({ state, props }) {
    const allele = state.get(`views.workflows.interpretation.data.alleles.${props.alleleId}`)
    const N = 50
    const igvLocus = `${allele.chromosome}:${
        allele.start_position <= N ? 1 : allele.start_position - N
    }-${allele.open_end_position + N + 1}`
    state.set('views.workflows.visualization.igv.locus', igvLocus)
}
