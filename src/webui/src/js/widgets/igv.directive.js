/* jshint esnext: true */

import igv from 'igv/dist/igv.js'
import { Directive, Inject } from '../ng-decorators'
import { deepCopy } from '../util'

const getIgvLocus = (locus) => {
    const fallBackLocus = '1:1000'
    if (!locus) {
        return fallBackLocus
    }
    return `${locus.chr}:${locus.pos}`
}

/**
 * Directive for displaying igv.js
 */
@Directive({
    selector: 'igv',
    scope: {
        locus: '=',
        tracks: '=',
        reference: '='
    },
    template: '<div></div>',
    link: (scope, elem) => {
        var defaults = {
            showNavigation: true,
            showRuler: true,
            showCenterGuide: true,
            showCursorTrackingGuide: true,
            doubleClickDelay: 300,
            minimumBases: 50,
            promisified: true,
            loadDefaultGenomes: false
        }

        let options = {
            tracks: [],
            reference: scope.reference,
            locus: getIgvLocus(scope.locus),
            showKaryo: true,
            search: {
                url: '/api/v1/igv/search/?q=$FEATURE$',
                coords: 0
            }
        }

        Object.assign(defaults, options)
        let browserPromise = igv.createBrowser(elem.children()[0], defaults)

        browserPromise.then((browser) => {
            // Make sure to remove browser upon destroy,
            // memory consumption can be 100's of MBs
            elem.on('$destroy', () => {
                // Use timeout of 5 seconds to allow igv tasks to finish
                setTimeout(() => igv.removeBrowser(browser), 5000)
            })

            scope.$watch(
                () => {
                    return scope.locus
                },
                () => {
                    browser.search(getIgvLocus(scope.locus))
                }
            )

            // poor-mans mutex for loading tracks
            let loading = false

            const updateTracks = () => {
                // an update is in progress - it will trigger this function once completed
                if (loading) {
                    return
                }

                const _onLoadComplete = () => {
                    loading = false
                    updateTracks()
                }
                const _head1 = ([first]) => first

                // load tracks
                const currentTrackNames = browser.trackViews
                    .filter((tv) => !['ideogram', 'sequence', 'ruler'].includes(tv.track.type))
                    .map((tv) => tv.track.name)
                // remove tracks that are not in the state anymore
                currentTrackNames
                    .filter(
                        (name) =>
                            !Object.values(scope.tracks).find((cfg) => cfg.igvcfg.name === name)
                    )
                    .forEach((name) => {
                        browser.removeTrackByName(name)
                    })
                // add tracks
                const toAddTracks = Object.entries(scope.tracks)
                    .filter(([id, cfg]) => cfg.type != 'roi')
                    .filter(([id, cfg]) => !currentTrackNames.includes(cfg.igvcfg.name))
                    .map(([id, cfg]) => cfg.igvcfg)
                // load only one track - remaining tracks in next iterations
                const toAddTrack = _head1(toAddTracks)
                if (toAddTrack) {
                    loading = true
                    browser.loadTrack(deepCopy(toAddTrack)).then(_onLoadComplete)
                }

                // load ROIs
                const currentRoiNames = (browser.roi ? browser.roi : []).map((roi) => roi.name)
                // remove ROIs that are not in the state anymore
                currentRoiNames
                    .filter(
                        (name) =>
                            !Object.values(scope.tracks).find((cfg) => cfg.igvcfg.name === name)
                    )
                    .forEach((name) => {
                        browser.removeROI({ name: name })
                    })
                const toAddRois = Object.entries(scope.tracks)
                    .filter(([id, cfg]) => cfg.type == 'roi')
                    .filter(([id, cfg]) => !currentRoiNames.includes(cfg.igvcfg.name))
                    .map(([id, cfg]) => cfg.igvcfg)
                const toAddRoi = _head1(toAddRois)
                if (toAddRoi) {
                    loading = true
                    browser.loadROI(deepCopy(toAddRois)).then(_onLoadComplete)
                }
            }

            // Load initial tracks
            updateTracks()

            scope.$watch('tracks', updateTracks)

            // allow zoom with mouse wheel
            const igvContainer = document.querySelector('.igv-column-container')
            if (igvContainer) {
                igvContainer.onwheel = (event) => {
                    // zoom only in combination with key
                    if (!event.altKey && !event.shiftKey) {
                        return
                    }
                    event.preventDefault()
                    const scaleFactor = 1.2
                    browser.zoomWithScaleFactor(event.deltaY > 0 ? scaleFactor : 1 / scaleFactor)
                }
            }
        })
    }
})
@Inject('Config')
class IgvController {
    constructor() {}
}

export { IgvController }
