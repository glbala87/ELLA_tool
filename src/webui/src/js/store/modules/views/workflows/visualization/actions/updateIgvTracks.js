export default function updateIgvTracks({ state }) {
    const tracks = state.get('views.workflows.visualization.tracks')
    if (!tracks) {
        return
    }
    const selectedTracks = Object.entries(tracks)
        .filter(([id, cfg]) => cfg.selected)
        .map(([id, cfg]) => [id, cfg.igv])
        .reduce((obj, [k, v]) => {
            obj[k] = v
            return obj
        }, {})
    state.set(`views.workflows.visualization.igv.tracks`, selectedTracks)
}
