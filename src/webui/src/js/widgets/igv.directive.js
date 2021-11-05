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
        roi: '=',
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
            roi: [],
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
            browser.loadROI(scope.roi)
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
                const currentTrackNames = browser.trackViews
                    .filter((tv) => !['ideogram', 'sequence', 'ruler'].includes(tv.track.type))
                    .map((tv) => tv.track.name)
                // remove tracks that are not in the state anymore
                currentTrackNames
                    .filter((name) => !scope.tracks.find((t) => t.name === name))
                    .forEach((name) => {
                        browser.removeTrackByName(name)
                    })
                // add tracks
                const toAddTracks = scope.tracks.filter((t) => !currentTrackNames.includes(t.name))
                // load only one track - remaining tracks in next iterations
                const _head1 = ([first]) => first
                const toAddTrack = _head1(toAddTracks)
                if (toAddTrack) {
                    loading = true
                    // load tracks async
                    browser.loadTrack(deepCopy(toAddTrack)).then(() => {
                        loading = false
                        // recheck whenever we previously had a change
                        updateTracks()
                    })
                }
            }

            // Load initial tracks
            updateTracks()

            scope.$watchCollection('tracks', updateTracks)

            // allow zoom with mouse wheel
            const igvContainer = document.querySelector('.igv-column-container')
            if (igvContainer) {
                igvContainer.onwheel = (event) => {
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
