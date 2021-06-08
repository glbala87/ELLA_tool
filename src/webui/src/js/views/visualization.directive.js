/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './visualization.ngtmpl.html' // eslint-disable-line no-unused-vars

// array of unique preset ids
const _getPresetIds = (tracks) => {
    return Compute(tracks, (tracks) => {
        if (!tracks) {
            return []
        }
        const r = Object.values(tracks)
            .flat()
            .map((e) => e.config.presets)
            .flat()
            .filter((e) => e !== undefined)
        return [...new Set(r)]
    })
}

const _getCurrPresetModel = (tracks) => {
    return Compute(tracks, (tracks) => {
        console.log(`_getCurrPresetModel`)
        const _getTrackId = (categoryId, trackIdx) => {
            return `${categoryId}_${trackIdx}`
        }
        // object: preset_ID -> Set[track_ID_1, track_ID_2, ... ]
        const _getPresetTracks = () => {
            const r = {}
            if (!tracks) {
                return r
            }
            Object.keys(tracks).forEach((trackCatId) => {
                tracks[trackCatId].forEach((track, trackIdx) => {
                    if (track.config.presets === undefined) {
                        return
                    }
                    track.config.presets.forEach((presetId) => {
                        if (!r.hasOwnProperty(presetId)) {
                            r[presetId] = new Set()
                        }
                        r[presetId].add(_getTrackId(trackCatId, trackIdx))
                    })
                })
            })
            return r
        }
        // set of track IDs: Set[track_ID_1, track_ID_2, ... ]
        const _getSelectedTracks = () => {
            const r = new Set()
            if (!tracks) {
                return r
            }
            Object.keys(tracks).forEach((trackCatId) => {
                tracks[trackCatId].forEach((track, trackIdx) => {
                    if (track.selected) {
                        r.add(_getTrackId(trackCatId, trackIdx))
                    }
                })
            })
            return r
        }
        const _equalSet = (a, b) => a.size === b.size && [...a].every((value) => b.has(value))
        const presetTracks = _getPresetTracks()
        const currTrackSelection = _getSelectedTracks()
        console.log(currTrackSelection)
        for (let presetId of Object.keys(presetTracks)) {
            if (_equalSet(currTrackSelection, presetTracks[presetId])) {
                console.log(`_getCurrPresetModel selected: ${presetId}`)
                return presetId
            }
        }
        // no preset selected
        console.log(`_getCurrPresetModel selected: ${null}`)
        return null
    })
}

const _updateTrackSelections = (tracks, setectedPresetId, shownTracksChanged) => {
    console.log('_updateTrackSelections')
    Object.keys(tracks).forEach((k) => {
        tracks[k].forEach((track) => {
            const sel =
                track.config.presets !== undefined &&
                track.config.presets.includes(setectedPresetId)
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
            presetIds: _getPresetIds(state`views.workflows.visualization.tracks`),
            presetModel: _getCurrPresetModel(state`views.workflows.visualization.tracks`),
            shownTracksChanged: signal`views.workflows.visualization.igvTrackViewChanged`
        },
        'Visualization',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    activePresetId: function(newPresetId) {
                        console.log(
                            `activePresetId args=${arguments.length} ctrl.presetModel=${$ctrl.presetModel}`
                        )
                        if (arguments.length) {
                            _updateTrackSelections(
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
