/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './visualization.ngtmpl.html' // eslint-disable-line no-unused-vars

// object: preset_ID -> Set[track_inf1, track_inf2, ... ]
const getPresetByTrackId = (tracks) => {
    const r = {}
    if (!tracks) {
        return r
    }
    Object.entries(tracks).forEach(([trackId, trackCfg]) => {
        trackCfg.presets.forEach((presetId) => {
            if (!r.hasOwnProperty(presetId)) {
                r[presetId] = new Set()
            }
            r[presetId].add(trackId)
        })
    })
    return r
}

// array of unique preset ids
const getPresets = (tracks) => {
    return Compute(tracks, (tracks) => {
        const r = {}
        const preset2TracksId = getPresetByTrackId(tracks)
        Object.keys(preset2TracksId)
            // sort default element to the front
            .reduce((acc, e) => (e == 'Default' ? [e, ...acc] : [...acc, e]), [])
            // convert to array - angularjs 1.x does not support Set
            .forEach((k) => {
                r[k] = Array.from(preset2TracksId[k])
            })
        return r
    })
}

const getCurrPresetModel = (tracks) => {
    return Compute(tracks, (tracks) => {
        // set of track IDs: Set[track_ID_1, track_ID_2, ... ]
        const _getSelectedTracks = (tracks) => {
            const r = new Set()
            if (!tracks) {
                return r
            }
            Object.entries(tracks).forEach(([trackId, trackCfg]) => {
                if (trackCfg.selected) {
                    r.add(trackId)
                }
            })
            return r
        }
        const _setContains = (a, b) => a.size >= b.size && [...b].every((value) => a.has(value))
        const preset2TracksId = getPresetByTrackId(tracks)
        const currTrackSelection = _getSelectedTracks(tracks)
        // init model
        const presetModel = {}
        // set status
        for (let presetId of Object.keys(preset2TracksId)) {
            presetModel[presetId] = _setContains(
                currTrackSelection,
                new Set([...preset2TracksId[presetId]]) // extract set of UIDs
            )
        }
        return presetModel
    })
}

app.component('visualization', {
    templateUrl: 'visualization.ngtmpl.html',
    controller: connect(
        {
            igvLocus: state`views.workflows.visualization.igv.locus`,
            igvTracks: state`views.workflows.visualization.igv.tracks`,
            roi: state`views.workflows.visualization.roi`,
            igvReference: state`views.workflows.visualization.igv.reference`,
            tracks: state`views.workflows.visualization.tracks`,
            presets: getPresets(state`views.workflows.visualization.tracks`),
            presetModel: getCurrPresetModel(state`views.workflows.visualization.tracks`),
            shownTracksChanged: signal`views.workflows.visualization.igvTrackViewChanged`
        },
        'Visualization',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    togglePreset: function(presetId) {
                        const show = $ctrl.presetModel[presetId] // no need to negate, model is already changed
                        const tracksToUpdate = []
                        Object.entries($ctrl.tracks).forEach(([trackId, trackCfg]) => {
                            if (!trackCfg.presets.includes(presetId)) {
                                return
                            }
                            if (show) {
                                // activate track
                                tracksToUpdate.push({
                                    trackId: trackId,
                                    show: true
                                })
                            } else {
                                // only deactivate if not referenced anymore
                                const associatedActivePresets = trackCfg.presets.filter(
                                    (e) => $ctrl.presetModel[e]
                                )
                                if (associatedActivePresets.length == 0) {
                                    tracksToUpdate.push({
                                        trackId: trackId,
                                        show: false
                                    })
                                }
                            }
                        })
                        $ctrl.shownTracksChanged({ tracksToUpdate })
                    },
                    hasEntries: function(obj) {
                        return obj && Object.keys(obj).length > 0
                    }
                })
            }
        ]
    )
})
