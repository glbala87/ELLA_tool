/* jshint esnext: true */

import igv from 'igv/dist/igv.js'
import { Directive, Inject } from '../ng-decorators'

const getIgvLocus = (locus) => `${locus.chr}:${locus.pos}`

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
    template: '<div class="igv-container"></div>',
    link: (scope, elem, attrs) => {
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
                    if (scope.locus) {
                        browser.search(getIgvLocus(scope.locus))
                    }
                }
            )

            // Watch changes to shown tracks
            scope.$watchCollection('tracks', () => {
                // IGV has two internal tracks with empty string as track names
                // These should be left alone...
                const currentTrackNames = browser.trackViews
                    .filter((tv) => !['ideogram', 'sequence', 'ruler'].includes(tv.track.type))
                    .map((tv) => tv.track.name)
                const removedNames = currentTrackNames.filter(
                    (name) => !scope.tracks.find((t) => t.name === name)
                )
                const toAddTracks = scope.tracks.filter((t) => !currentTrackNames.includes(t.name))

                for (const name of removedNames) {
                    browser.removeTrackByName(name)
                }

                for (const track of toAddTracks) {
                    browser.loadTrack(track)
                }
            })

            // allow zoom with mouse wheel
            document.querySelector('.igv-track-container').onwheel = (event) => {
                event.preventDefault()
                const scaleFactor = 1.2
                browser.zoom(event.deltaY > 0 ? scaleFactor : 1 / scaleFactor)
            }
        })
    }
})
@Inject('Config')
export class IgvController {
    constructor() {}
}
