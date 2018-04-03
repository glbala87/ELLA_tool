/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

@Directive({
    selector: 'genome-browser-widget',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/genomeBrowserWidget.ngtmpl.html'
})
@Inject('$scope')
export class GenomeBrowserWidgetController {
    constructor($scope) {
        $scope.$watch('allele', (allele) => {
            if (allele) {
                this.refresh()
            }
        })

        setTimeout(() => {
            this.setupBrowser()
            this.refresh()
        }, 500)
    }

    setupBrowser() {
        this.browser = new Browser({
            pageName: 'dalliance-holder', // Target element ID.

            chr: '1',
            viewStart: 0,
            viewEnd: 10,
            cookieKey: 'human-grc_h37',

            coordSystem: {
                speciesName: 'Human',
                taxon: 9606,
                auth: 'GRCh',
                version: '37',
                ucscName: 'hg19'
            },

            sources: [
                {
                    name: 'Genome',
                    twoBitURI: 'http://www.biodalliance.org/datasets/hg19.2bit',
                    tier_type: 'sequence',
                    provides_entrypoints: true,
                    pinned: true
                },
                {
                    name: 'GENCODE',
                    bwgURI: 'http://www.biodalliance.org/datasets/gencode.bb',
                    stylesheet_uri: 'http://www.biodalliance.org/stylesheets/gencode.xml',
                    collapseSuperGroups: true,
                    trixURI: 'http://www.biodalliance.org/datasets/geneIndex.ix'
                },
                {
                    name: 'Repeats',
                    desc: 'Repeat annotation from RepeatMasker',
                    bwgURI: 'http://www.biodalliance.org/datasets/repeats.bb',
                    stylesheet_uri: 'http://www.biodalliance.org/stylesheets/bb-repeats.xml',
                    forceReduction: -1
                },
                {
                    name: 'SNPs',
                    tier_type: 'ensembl',
                    species: 'human',
                    type: 'variation',
                    featureInfoPlugin: function(f, info) {
                        if (f.id) {
                            info.add(
                                'SNP',
                                makeElement('a', f.id, {
                                    href:
                                        'http://www.ensembl.org/Homo_sapiens/Variation/Summary?v=' +
                                        f.id,
                                    target: '_newtab'
                                })
                            )
                        }
                    }
                },
                {
                    name: 'Conservation',
                    bwgURI: 'http://www.biodalliance.org/datasets/phastCons46way.bw',
                    noDownsample: true
                }
            ],

            noOptions: true,
            noTrackAdder: true,
            noTrackEditor: true,
            noExport: true,
            noLeapButtons: true
        })
    }

    refresh() {
        if (this.browser && this.allele) {
            this.setLocation(this.allele)
        }
    }

    setLocation(allele) {
        this.browser.setLocation(
            allele.chromosome,
            allele.start_position - 49,
            allele.open_end_position + 50
        )
    }

    addBAMTrack(bamFile) {
        this.browser.addTier({
            name: 'BAM',
            bamURI: bamFile,
            tier_type: 'bam',
            style: [
                {
                    type: 'density',
                    zoom: 'low',
                    style: {
                        glyph: 'HISTOGRAM',
                        COLOR1: 'black',
                        COLOR2: 'red',
                        HEIGHT: 30
                    }
                },
                {
                    type: 'density',
                    zoom: 'medium',
                    style: {
                        glyph: 'HISTOGRAM',
                        COLOR1: 'black',
                        COLOR2: 'red',
                        HEIGHT: 30
                    }
                },
                {
                    type: 'bam',
                    zoom: 'high',
                    style: {
                        glyph: '__SEQUENCE',
                        FGCOLOR: 'black',
                        BGCOLOR: 'blue',
                        HEIGHT: 8,
                        BUMP: true,
                        LABEL: false,
                        ZINDEX: 20,
                        __SEQCOLOR: 'mismatch'
                    }
                }
            ]
        })
    }
}
