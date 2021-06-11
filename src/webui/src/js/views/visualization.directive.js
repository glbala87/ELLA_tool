/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './visualization.ngtmpl.html' // eslint-disable-line no-unused-vars

const getTrackId = (categoryId, trackIdx) => {
    // stich track index to track category ID - trackIdx is an int
    return `${categoryId}_${trackIdx}`
}

// object: preset_ID -> Set[track_ID_1, track_ID_2, ... ]
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
                r[presetId].add(getTrackId(trackCatId, trackIdx))
            })
        })
    })
    return r
}

// array of unique preset ids
const getPresetIds = (tracks) => {
    // sort default element to the front
    return Compute(tracks, (tracks) =>
        Object.keys(getPresetTracks(tracks)).reduce(
            (acc, e) => (e == 'Default' ? [e, ...acc] : [...acc, e]),
            []
        )
    )
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
                        r.add(getTrackId(trackCatId, trackIdx))
                    }
                })
            })
            return r
        }
        const _equalSet = (a, b) => a.size === b.size && [...a].every((value) => b.has(value))
        const presetTracks = getPresetTracks(tracks)
        const currTrackSelection = _getSelectedTracks(tracks)
        for (let presetId of Object.keys(presetTracks)) {
            if (_equalSet(currTrackSelection, presetTracks[presetId])) {
                return presetId
            }
        }
        // no preset selected
        return null
    })
}

const updateTrackSelections = (tracks, setectedPresetId, shownTracksChanged) => {
    Object.keys(tracks).forEach((k) => {
        tracks[k].forEach((track) => {
            const sel = track.presets !== undefined && track.presets.includes(setectedPresetId)
            shownTracksChanged({ type: k, id: track.id, show: sel })
        })
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
            presetIds: getPresetIds(state`views.workflows.visualization.tracks`),
            presetModel: getCurrPresetModel(state`views.workflows.visualization.tracks`),
            shownTracksChanged: signal`views.workflows.visualization.igvTrackViewChanged`
        },
        'Visualization',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    activePresetId: function(newPresetId) {
                        if (arguments.length) {
                            updateTrackSelections(
                                $ctrl.tracks,
                                newPresetId,
                                $ctrl.shownTracksChanged
                            )
                        }
                        return $ctrl.presetModel
                    }
                })
            }
        ]
    )
})
