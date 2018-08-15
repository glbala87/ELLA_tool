/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './igv.ngtmpl.html'
import igv from 'igv';

app.component('visualization', {
    templateUrl: 'igv.ngtmpl.html',
    controller: connect(
        {
            igvLocus: state`views.workflows.igv.locus`,
            tracks: state`views.workflows.igv.tracks`,
            igvReference: state`views.workflows.igv.reference`,
            shownTracksChanged: signal`views.workflows.igvTrackViewChanged`
        },
        'IGV'
    )
})

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

        var defaults =  {
            showNavigation: true,
            showRuler: true,
            showCenterGuide: true,
            showCursorTrackingGuide: true,
            doubleClickDelay: 300,
            minimumBases: 50,
            promisified: true,
        }

        let trackConfigs = scope.tracks.filter((t) => t.show).map((x) => x.config)

        let options = {
            tracks: trackConfigs,
            reference: scope.reference,
            locus: scope.locus,
        }

        Object.assign(defaults, options)
        let browserPromise = igv.createBrowser(elem.children()[0], defaults)

        browserPromise.then( (browser) => {
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
            scope.$watch(
                () => {
                    return scope.tracks
                },
                () => {
                    let igvShownTracks = browser.trackViews.map((tv) => tv.track.name)

                    let tracksToShow = scope.tracks.map((t) => t.config.name).filter((t) => igvShownTracks.indexOf(t) === -1)
                    let tracksToHide = scope.tracks.filter((t) => t.show === false).map((t) => t.config.name).filter((t) => igvShownTracks.indexOf(t) !== -1)

                    for (let trackName of tracksToHide) {
                        browser.removeTrackByName(trackName)
                    }

                    for (let trackName of tracksToShow) {
                        let trackConfig = scope.tracks.find((t) => t.config.name === trackName).config
                        browser.loadTrack(trackConfig)
                    }
                },
                true
            )


        })
    }
})
@Inject('Config')
export class IgvController {
    constructor() {}
}
