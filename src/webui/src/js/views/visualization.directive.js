/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './visualization.ngtmpl.html' // eslint-disable-line no-unused-vars

const getTrackUid = (categoryId, trackIdx) => {
    // stich track index to track category ID - trackIdx is an int
    return `${categoryId}_${trackIdx}`
}

// object: preset_ID -> Set[track_inf1, track_inf2, ... ]
const getPresetTracks = (tracks) => {
    const r = {}
    if (!tracks) {
        return r
    }
    Object.keys(tracks).forEach((trackCatId) => {
        tracks[trackCatId].forEach((track, trackIdx) => {
            if (track.presets === undefined) {
                return
            }
            track.presets.forEach((presetId) => {
                if (!r.hasOwnProperty(presetId)) {
                    r[presetId] = new Set()
                }
                const trackInfo = {
                    uid: getTrackUid(trackCatId, trackIdx),
                    data: track,
                    categoryId: trackCatId,
                    index: trackIdx
                }
                r[presetId].add(trackInfo)
            })
        })
    })
    return r
}

// array of unique preset ids
const getPresets = (tracks) => {
    return Compute(tracks, (tracks) => {
        const r = {}
        const presetTracks = getPresetTracks(tracks)
        Object.keys(presetTracks)
            // sort default element to the front
            .reduce((acc, e) => (e == 'Default' ? [e, ...acc] : [...acc, e]), [])
            // convert to array - angularjs 1.x does not support Set
            .forEach((k) => {
                r[k] = Array.from(presetTracks[k])
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
            Object.keys(tracks).forEach((trackCatId) => {
                tracks[trackCatId].forEach((track, trackIdx) => {
                    if (track.selected) {
                        r.add(getTrackUid(trackCatId, trackIdx))
                    }
                })
            })
            return r
        }
        const _setContains = (a, b) => a.size >= b.size && [...b].every((value) => a.has(value))
        const presetTracks = getPresetTracks(tracks)
        const currTrackSelection = _getSelectedTracks(tracks)
        // init model
        const presetModel = {}
        // set status
        for (let presetId of Object.keys(presetTracks)) {
            presetModel[presetId] = _setContains(
                currTrackSelection,
                new Set([...presetTracks[presetId]].map((e) => e.uid)) // extract set of UIDs
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
                        const _equalSet = (a, b) =>
                            a.size === b.size && [...a].every((value) => b.has(value))
                        Object.keys($ctrl.tracks).forEach((trackCategory) => {
                            $ctrl.tracks[trackCategory].forEach((track, trackIdx) => {
                                if (track.presets === undefined) {
                                    return
                                }
                                if (!track.presets.includes(presetId)) {
                                    return
                                }
                                if (show) {
                                    // activate track
                                    tracksToUpdate.push({
                                        type: trackCategory,
                                        id: track.id,
                                        show: true
                                    })
                                } else {
                                    // only deactivate if not referenced anymore
                                    const associatedActivePresets = track.presets.filter(
                                        (e) => $ctrl.presetModel[e]
                                    )
                                    if (associatedActivePresets.length == 0) {
                                        tracksToUpdate.push({
                                            type: trackCategory,
                                            id: track.id,
                                            show: false
                                        })
                                    }
                                }
                            })
                        })
                        $ctrl.shownTracksChanged({ tracksToUpdate })
                    }
                })
            }
        ]
    )
})
