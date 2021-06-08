/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './visualization.ngtmpl.html' // eslint-disable-line no-unused-vars

const getPresetIds = (tracks) => {
    return Compute(tracks, (tracks) => {
        if (!tracks) {
            return []
        }
        const r = Object.values(tracks)
            .flat()
            .map((e) => e.preset)
            .flat()
            .filter((e) => e !== undefined)
        return [...new Set(r)]
    })
}

const _getCurrPresetModel = (tracks) => {
    console.log(`_getCurrPresetModel`)
    const _getTrackId = (categoryId, trackIdx) => {
        return `${categoryId}_${trackIdx}`
    }
    const _getPresetTracks = () => {
        const r = {}
        if (!tracks) {
            return r
        }
        Object.keys(tracks).forEach((trackCatId) => {
            tracks[trackCatId].forEach((track, trackIdx) => {
                if (track.preset === undefined) {
                    return
                }
                track.preset.forEach((presetId) => {
                    if (!r.hasOwnProperty(presetId)) {
                        r[presetId] = new Set()
                    }
                    r[presetId].add(_getTrackId(trackCatId, trackIdx))
                })
            })
        })
        return r
    }
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
}

const _updateTrackSelections = (tracks, setectedPresetId) => {
    console.log('_updateTrackSelections')
    Object.keys(tracks).forEach((k) => {
        tracks[k].forEach((track) => {
            const sel = track.preset !== undefined && track.preset.includes(setectedPresetId)
            track.selected = sel
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
            shownTracksChanged: signal`views.workflows.visualization.igvTrackViewChanged`
        },
        'Visualization',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                let _model = null

                Object.assign($ctrl, {
                    activePresetId: function(newPresetId) {
                        console.log(`activePresetId ${arguments.length}`)
                        if (arguments.length) {
                            _model = newPresetId
                            _updateTrackSelections($ctrl.tracks, newPresetId)
                        } else {
                            _model = _getCurrPresetModel($ctrl.tracks)
                        }
                        console.log(`activePresetId ${_model}`)
                        return _model
                    }
                })
            }
        ]
    )
})
