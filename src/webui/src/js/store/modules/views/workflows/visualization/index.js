import { Module } from 'cerebral'
import igvTrackViewChanged from './signals/igvTrackViewChanged'

export default Module({
    state: {
        igv: {
            reference: null,
            locus: null,
            tracks: []
        },
        tracks: null
    },
    signals: {
        igvTrackViewChanged
    }
})
