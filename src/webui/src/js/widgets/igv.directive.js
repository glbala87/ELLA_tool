/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';


/**
 * Directive for displaying igv.js
 */
@Directive({
    selector: 'igv',
    scope: {
        chrom: '@?',  // Default start chromosome (e.g. '12')
        pos: '@?',  // Default start position (e.g. '123-234')
    },
    template: '<div class="igv-container"></div>',
    link: (scope, elem, attrs) => {
        var options = {
            showNavigation: true,
            showRuler: true,
            genome: "hg19",
            locus: "chr12:98,997,292-98,997,392",
            tracks: [
                {
                    name: "Genes",
                    url: "//s3.amazonaws.com/igv.broadinstitute.org/annotations/hg19/genes/gencode.v18.collapsed.bed",
                    displayMode: "EXPANDED"

                },                        {
                    url: 'https://data.broadinstitute.org/igvdata/BodyMap/hg19/IlluminaHiSeq2000_BodySites/brain_merged/accepted_hits.bam',
                    name: 'Brain (BodyMap)'
                }

            ],
            doubleClickDelay: 300,
        };
        igv.createBrowser(elem.children()[0], options);
    }
})
@Inject('Config')
export class IgvController {

    constructor() {

    }

}
