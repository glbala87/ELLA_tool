export default function updateIgvLocus({ state, props }) {
    const allele = state.get(`views.workflows.interpretation.data.alleles.${props.alleleId}`)
    const N = 50
    const igvLocus = `${allele.chromosome}:${allele.vcf_pos}`
    state.set('views.workflows.visualization.igv.locus', igvLocus)
}
