import { deepCopy } from '../../../../../../util'
import { IGVBrowser } from '../../../../../../widgets/igv.directive'

export default function showHideTracks({ state, props }) {
    const { tracksToUpdate } = props
    if (!tracksToUpdate || tracksToUpdate.length == 0) {
        return
    }
    const tracks = deepCopy(state.get(`views.workflows.visualization.tracks`))
    if (!tracks || !IGVBrowser) {
        return
    }

    const loadPromises = []
    tracksToUpdate.forEach((trackToUpdate) => {
        const { type, id, show } = trackToUpdate
        if (tracks[type]) {
            const trackIdx = tracks[type].findIndex((i) => i.id === id)
            if (trackIdx >= 0) {
                tracks[type][trackIdx].selected = show
                if (show) {
                    // loadTrack returns a Promise
                    IGVBrowser.loadTrack(tracks[type][trackIdx].config)
                } else {
                    IGVBrowser.removeTrackByName(tracks[type][trackIdx].config.name)
                }
            }
        }
    })
    state.set(`views.workflows.visualization.tracks`, tracks)
}
