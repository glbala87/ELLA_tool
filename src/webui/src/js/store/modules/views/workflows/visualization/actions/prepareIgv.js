import thenBy from 'thenby'

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
    for (const [category, categoryTracks] of Object.entries(trackConfigs.result)) {
        if (category != 'roi') {
            for (const track of categoryTracks) {
                const finalizedTrack = {
                    id: track.id,
                    selected: 'show' in track ? Boolean(track.show) : false,
                    config: track,
                    presets: track.presets !== undefined ? track.presets : []
                }
                // cleanup
                delete finalizedTrack.config.show
                delete finalizedTrack.config.presets
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
                if (!finalizedTracks.hasOwnProperty(category)) {
                    finalizedTracks[category] = []
                }
                finalizedTracks[category].push(finalizedTrack)
            }
        }
    }
    for (const categoryTracks of Object.values(finalizedTracks)) {
        categoryTracks.sort(thenBy((t) => t.config.order || 99999))
    }
    state.set('views.workflows.visualization.roi', trackConfigs.result.roi)
    state.set('views.workflows.visualization.tracks', finalizedTracks)
}
