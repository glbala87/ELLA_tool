export default function updateIgvTracks({ state }) {
    const tracks = state.get('views.workflows.visualization.tracks')
    if (!tracks) {
        return
    }
    const allTracks = Object.values(tracks)
        .reduce((p, c) => {
            return p.concat(c)
        }, [])
        .filter((t) => t.selected)
        .map((t) => t.config)
    state.set(`views.workflows.visualization.igv.tracks`, allTracks)
}
