/* jshint esnext: true */

import igv from 'igv/dist/igv.js'
import { Directive, Inject } from '../ng-decorators'

/**
 * Directive for displaying igv.js
 */
@Directive({
    selector: 'igv',
    scope: {
        locus: '=',
        tracks: '=',
        shownTracks: '=',
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
            promisified: true
        }

        let options = {
            tracks: [],
            reference: scope.reference,
            locus: scope.locus
        }

        Object.assign(defaults, options)
        let browserPromise = igv.createBrowser(elem.children()[0], defaults)

        browserPromise.then((browser) => {
            scope.$watch(
                () => {
                    return scope.locus
                },
                () => {
                    if (scope.locus) {
                        browser.search(scope.locus)
                    }
                }
            )

            // Watch changes to shown tracks
            scope.$watchCollection('tracks', () => {
                // IGV has two internal tracks with empty string as track names
                // These should be left alone...
                const currentTrackNames = browser.trackViews
                    .map((tv) => tv.track.name)
                    .filter((t) => t != '')
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
        })
    }
})
@Inject('Config')
export class IgvController {
    constructor() {}
}
