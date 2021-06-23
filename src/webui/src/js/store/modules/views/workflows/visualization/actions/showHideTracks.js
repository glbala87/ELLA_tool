import { deepCopy } from '../../../../../../util'

export default function showHideTracks({ state, props }) {
    const { tracksToUpdate } = props
    if (!tracksToUpdate || tracksToUpdate.length == 0) {
        return
    }
    const tracks = deepCopy(state.get(`views.workflows.visualization.tracks`))
    if (!tracks) {
        return
    }
    tracksToUpdate.forEach((trackToUpdate) => {
        const { type, id, show } = trackToUpdate
        if (tracks[type]) {
            const trackIdx = tracks[type].findIndex((i) => i.id === id)
            if (trackIdx >= 0) {
                tracks[type][trackIdx].selected = show
            }
        }
    })
    state.set(`views.workflows.visualization.tracks`, tracks)
}
