/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';


/**
 * Directive for displaying igv.js
 */
@Directive({
    selector: 'igv',
    scope: {
        options: '=', // igv options
        chrom: '@?',  // Default start chromosome (e.g. '12')
        pos: '@?',  // Default start position (e.g. '123-234')
    },
    template: '<div class="igv-container"></div>',
    link: (scope, elem, attrs) => {
        var defaults = {
            showNavigation: true,
            showRuler: true,
            genome: "hg19",
            showCenterGuide: true,
            showCursorTrackingGuide: true,
            doubleClickDelay: 300,
        };
        Object.assign(defaults, scope.options, {
            locus: `chr${scope.chrom}:${scope.pos}`,
        });
        console.log(defaults);
        igv.createBrowser(elem.children()[0], defaults);
    }
})
@Inject('Config')
export class IgvController {

    constructor() {
    }

}
