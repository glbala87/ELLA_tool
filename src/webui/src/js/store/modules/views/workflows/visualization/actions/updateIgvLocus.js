export default function updateIgvLocus({ state, props }) {
    const allele = state.get(`views.workflows.interpretation.data.alleles.${props.alleleId}`)
    const N = 50
    const padding = Math.max(N / 2, 0.1 * allele.length)
    const start = Math.max(allele.vcf_pos - padding, 0)
    const end = allele.vcf_pos + allele.length + padding
    const igvLocus = {
        chr: allele.chromosome,
        pos: `${start}-${Math.abs(end)}`
    }

    state.set('views.workflows.visualization.igv.locus', igvLocus)
}
