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

    const dynamicTracksResult = await http.get(
        `igv/tracks/${analysis.id}?allele_ids=${Object.keys(alleles).join(',')}`
    )

    const _appendFinalizedTracks = (tracks, cfgTracks) => {
        for (const [category, categoryTracks] of Object.entries(cfgTracks)) {
            for (const track of categoryTracks) {
                const finalizedTrack = {
                    id: track.id,
                    selected: 'show' in track ? track.show : false,
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
                // append
                if (!tracks.hasOwnProperty(category)) {
                    tracks[category] = []
                }
                tracks[category].push(finalizedTrack)
            }
        }
    }

    const finalizedTracks = {}
    _appendFinalizedTracks(finalizedTracks, dynamicTracksResult.result)

    for (const categoryTracks of Object.values(finalizedTracks)) {
        categoryTracks.sort(thenBy((t) => t.config.order || 99999))
    }
    state.set('views.workflows.visualization.tracks', finalizedTracks)
}
