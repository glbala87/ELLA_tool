export default async function prepareIgv({ state, http }) {
    const igvReferenceConfig = state.get('app.config.igv.reference')
    state.set('views.workflows.visualization.igv.reference', {
        id: 'hg19',
        fastaURL: igvReferenceConfig.fastaURL,
        cytobandURL: igvReferenceConfig.cytobandURL
    })

    const analysis = state.get('views.workflows.data.analysis')
    const alleles = state.get('views.workflows.interpretation.data.alleles')

    const trackConfigs = await http.get(
        `igv/tracks/${analysis.id}?allele_ids=${alleles ? Object.keys(alleles).join(',') : ''}`
    )
    const finalizedTracks = {}
    for (const [trackId, trackConfig] of Object.entries(trackConfigs.result)) {
        const finalizedTrack = {
            selected: 'show' in trackConfig ? Boolean(trackConfig.show) : false,
            igv: 'igv' in trackConfig ? trackConfig.igv : {},
            description: 'description' in trackConfig ? trackConfig.description : null,
            type: 'type' in trackConfig ? trackConfig.type : null,
            presets: 'presets' in trackConfig ? trackConfig.presets : []
        }
        // derive default preset
        if (finalizedTrack.selected) {
            const presetIdDefault = 'Default'
            finalizedTrack.presets = [presetIdDefault, ...finalizedTrack.presets]
        }
        // add a preset if no other presets were set
        const presetIdOther = 'Other'
        if (finalizedTrack.presets.length == 0) {
            finalizedTrack.presets = [presetIdOther]
        }
        // append
        finalizedTracks[trackId] = finalizedTrack
    }
    state.set('views.workflows.visualization.tracks', finalizedTracks)
}
