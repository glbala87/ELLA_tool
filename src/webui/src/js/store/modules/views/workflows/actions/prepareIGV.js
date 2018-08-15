const getAvailableTracks = (analysis, alleles) => {
    let tracks = []

    tracks.push({
        name: 'Gencode',
        url: 'api/v1/igv/gencode.v18.collapsed.bed',
        displayMode: 'EXPANDED'
    })

    tracks.push({
        name: 'Genepanel',
        type: 'annotation',
        url: `/api/v1/genepanel/${analysis.genepanel.name}/${
            analysis.genepanel.version
        }/gencode/`,
        format: 'bed',
        indexed: false,
        displayMode: 'EXPANDED',
        height: 60
    })

    tracks.push({
        name: 'Variants',
        url: `/api/v1/analyses/${analysis.id}/${
            analysis.samples[0].id
        }/vcf/?q=${encodeURIComponent(
            JSON.stringify({ allele_ids: Object.keys(alleles) })
        )}`,
        format: 'vcf',
        indexed: false,
        visibilityWindow: Number.MAX_VALUE
    })

    for (let sample of analysis.samples) {
        tracks.push({
            name: sample.identifier+" (HC)",
            url: `api/v1/samples/${sample.id}/bams/?haplotypeCaller=1`,
            colorBy: 'strand',
            indexURL: `api/v1/samples/${sample.id}/bams/?index=1&haplotypeCaller=1`,
            format: 'bam',
            alignmentRowHeight: 10
        })
        tracks.push({
            name: sample.identifier,
            url: `api/v1/samples/${sample.id}/bams/`,
            indexURL: `api/v1/samples/${sample.id}/bams/?index=1`,
            colorBy: 'strand',
            format: 'bam',
            alignmentRowHeight: 10,
            visibilityWindow: 2e4
        })
    }

    return tracks
}

function prepareIGV({state}) {
    const igvReferenceConfig = state.get('app.config.igv.reference')
    state.set('views.workflows.igv.reference', {
        id: 'hg19',
        fastaURL: igvReferenceConfig.fastaURL,
        cytobandURL: igvReferenceConfig.cytobandURL
    })

    const analysis = state.get('views.workflows.data.analysis')
    const alleles = state.get('views.workflows.data.alleles')

    const availableTracks = getAvailableTracks(analysis, alleles)
    let tracks = []
    for (let trackConfig of availableTracks) {
        tracks.push({
            show: true,
            config: trackConfig
        })
    }

    state.set('views.workflows.igv.tracks', tracks)
}
export default prepareIGV
