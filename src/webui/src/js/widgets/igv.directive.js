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

// abstract parent class
class TrackType {
    matchesType(type) {
        throw new Error('not implemented')
    }
    getIgvLoadedTrackIds(browser) {
        throw new Error('not implemented')
    }
    removeTrack(browser, trackId) {
        throw new Error('not implemented')
    }
    async loadTrack(browser, igvcfg) {
        throw new Error('not implemented')
    }
}
// "normal" tracks
class TrackTypeDefault extends TrackType {
    matchesType(type) {
        return type != 'roi'
    }
    getIgvLoadedTrackIds(browser) {
        console.log('TrackTypeDefault', 'getIgvLoadedTrackIds')
        return browser.trackViews
            .filter((tv) => !['ideogram', 'sequence', 'ruler'].includes(tv.track.type))
            .map((tv) => tv.track.name)
    }
    removeTrack(browser, trackId) {
        browser.removeTrackByName(trackId)
    }
    async loadTrack(browser, igvcfg) {
        await browser.loadTrack(deepCopy(igvcfg))
    }
}
// ROI (region of interest) tracks
class TrackTypeRoi extends TrackType {
    matchesType(type) {
        return type == 'roi'
    }
    getIgvLoadedTrackIds(browser) {
        console.log('TrackTypeRoi', 'getIgvLoadedTrackIds')
        return (browser.roi ? browser.roi : []).map((roi) => roi.name)
    }
    removeTrack(browser, trackId) {
        browser.removeROI({ name: trackId })
    }
    async loadTrack(browser, igvcfg) {
        await browser.loadROI(deepCopy(igvcfg))
    }
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

                const trackTypes = [new TrackTypeDefault(), new TrackTypeRoi()]
                for (let i = 0; i < trackTypes.length; i++) {
                    const trackType = trackTypes[i]
                    // list tracks ocf the current type
                    const igvLoadedTrackIds = trackType.getIgvLoadedTrackIds(browser)
                    // remove tracks that are not in the state anymore
                    igvLoadedTrackIds
                        .filter(
                            (trackId) =>
                                !Object.values(scope.tracks).find(
                                    (cfg) => cfg.igvcfg.name === trackId
                                )
                        )
                        .forEach((trackId) => {
                            trackType.removeTrack(browser, trackId)
                        })
                    // list tracks to add
                    const toAddTracks = Object.entries(scope.tracks)
                        .filter(([id, cfg]) => trackType.matchesType(cfg.type))
                        .filter(([id, cfg]) => !igvLoadedTrackIds.includes(cfg.igvcfg.name))
                        .map(([id, cfg]) => cfg.igvcfg)
                    const toAddTrack = _head1(toAddTracks)
                    // any track to add?
                    if (toAddTrack) {
                        loading = true
                        trackType.loadTrack(browser, toAddTrack).then(_onLoadComplete)
                        // remaining tracks will be handled in next call
                        return
                    }
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
