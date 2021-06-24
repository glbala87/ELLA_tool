/* jshint esnext: true */

import igv from 'igv/dist/igv.js'
import { Directive, Inject } from '../ng-decorators'

const getIgvLocus = (locus) => `${locus.chr}:${locus.pos}`

const onTrackclick = (track, popupData) => {
    if (!popupData || !popupData.length) {
        return false
    }
    if (track.id === 'classifications') {
        const ep = document.createElement('div')
        const alleleUrlInfo = {
            chromosome: null,
            genome_reference: null,
            vcf_pos: null,
            vcf_ref: null,
            vcf_alt: null,
            genepanel_name: null,
            genepanel_version: null
        }
        const _addRow = (eParent, rowkey, eValue, title = null) => {
            const erow = document.createElement('div')
            eParent.appendChild(erow)
            if (title) {
                erow.title = title
            }
            const es = document.createElement('span')
            es.innerHTML = rowkey
            erow.appendChild(es)
            const hspace = document.createTextNode('\u00A0\u00A0\u00A0') // hspace taken from ivg.js
            erow.appendChild(hspace)
            erow.appendChild(eValue)
        }
        popupData.forEach((d) => {
            if (typeof d === 'object' && d.name != undefined && d.value != undefined) {
                // save allele info for later
                if (d.name in alleleUrlInfo) {
                    alleleUrlInfo[d.name] = d.value
                    // flush buffer?
                    if (Object.values(alleleUrlInfo).every((e) => e !== null)) {
                        // create allele link
                        const ea = document.createElement('a')
                        const alleleId = `${alleleUrlInfo.chromosome}-${alleleUrlInfo.vcf_pos}-${alleleUrlInfo.vcf_ref}-${alleleUrlInfo.vcf_alt}`
                        ea.href =
                            `/workflows/variants/${alleleUrlInfo.genome_reference}/` +
                            `${alleleId}` +
                            `?gp_name=${alleleUrlInfo.genepanel_name}&gp_version=${alleleUrlInfo.genepanel_version}`
                        ea.innerHTML = alleleId
                        ea.target = '_blank'
                        _addRow(ep, 'Assessment', ea)
                        // reset buffer
                        Object.keys(alleleUrlInfo).forEach((k) => (alleleUrlInfo[k] = null))
                    }
                    return
                }
                if (d.name == 'Score') {
                    return
                }
                if (d.name == 'Name') {
                    d.name = 'Class'
                }
                if (d.name == 'date_created') {
                    d.name = 'Created'
                }
                _addRow(ep, d.name, document.createTextNode(d.value), d.value)
            } else if (typeof d === 'string') {
                const erow = document.createElement('div')
                ep.appendChild(erow)
                erow.innerHTML = d
            }
        })
        return ep.innerHTML
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
            // custom popover
            browser.on('trackclick', onTrackclick)

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

            let loadTrackPromises = []
            // Watch changes to shown tracks
            scope.$watchCollection('tracks', () => {
                // wait for tracks to be loaded
                Promise.all(loadTrackPromises).then(() => {
                    // IGV has two internal tracks with empty string as track names
                    // These should be left alone...
                    loadTrackPromises = []
                    const currentTrackNames = browser.trackViews
                        .filter((tv) => !['ideogram', 'sequence', 'ruler'].includes(tv.track.type))
                        .map((tv) => tv.track.name)
                    const removedNames = currentTrackNames.filter(
                        (name) => !scope.tracks.find((t) => t.name === name)
                    )
                    const toAddTracks = scope.tracks.filter(
                        (t) => !currentTrackNames.includes(t.name)
                    )

                    for (const name of removedNames) {
                        browser.removeTrackByName(name)
                    }
                    if (toAddTracks.length) {
                        loadTrackPromises.push(browser.loadTrackList(toAddTracks))
                    }
                })
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
