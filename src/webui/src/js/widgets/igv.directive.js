/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
//import igv from 'igv'

/**
 * Directive for displaying igv.js
 */
@Directive({
    selector: 'igv',
    scope: {
        options: '=', // igv options
        chrom: '@?', // Default start chromosome (e.g. '12')
        pos: '@?' // Default start position (e.g. '123-234')
    },
    template: '<div class="igv-container"></div>',
    link: (scope, elem, attrs) => {
        var defaults = {
            showNavigation: true,
            showRuler: true,
            showCenterGuide: true,
            showCursorTrackingGuide: true,
            doubleClickDelay: 300
        }
        Object.assign(defaults, scope.options, {
            locus: `${scope.chrom}:${scope.pos}`
        })
        igv.createBrowser(elem.children()[0], defaults)
    }
})
@Inject('Config')
export class IgvController {
    constructor() {}
}
