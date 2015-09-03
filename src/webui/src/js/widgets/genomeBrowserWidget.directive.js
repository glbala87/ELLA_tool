/* jshint esnext: true */

workbench.directive( 'genomeBrowserWidget', function () {
    return {
        restrict: 'E',
        scope: {
            allele: '='
        },
        templateUrl: 'ngtmpl/genomeBrowserWidget.ngtmpl.html',
        controller: GenomeBrowserWidgetVM,
        controllerAs: 'vm'
    };
} );


class GenomeBrowserWidgetVM {

    constructor( $scope ) {

        this.setAllele( $scope.allele );

        $scope.$watch( 'allele', allele => {
            if ( allele ) {
                this.setAllele( allele );
                this.setLocation( allele );
            }
        } );

        this.browser = new Browser( {
            pageName: 'dalliance-holder', // Target element ID.

            chr: '22',
            viewStart: 30000000,
            viewEnd: 30030000,
            cookieKey: 'human-grc_h37',

            coordSystem: {
                speciesName: 'Human',
                taxon: 9606,
                auth: 'GRCh',
                version: '37',
                ucscName: 'hg19',
            },

            sources: [ {
                name: 'Genome',
                twoBitURI: 'http://www.biodalliance.org/datasets/hg19.2bit',
                tier_type: 'sequence',
                provides_entrypoints: true,
                pinned: true
            }, {
                name: 'GENCODE',
                bwgURI: 'http://www.biodalliance.org/datasets/gencode.bb',
                stylesheet_uri: 'http://www.biodalliance.org/stylesheets/gencode.xml',
                collapseSuperGroups: true,
                trixURI: 'http://www.biodalliance.org/datasets/geneIndex.ix'
            }, {
                name: 'Repeats',
                desc: 'Repeat annotation from RepeatMasker',
                bwgURI: 'http://www.biodalliance.org/datasets/repeats.bb',
                stylesheet_uri: 'http://www.biodalliance.org/stylesheets/bb-repeats.xml',
                forceReduction: -1
            }, {
                name: 'SNPs',
                tier_type: 'ensembl',
                species: 'human',
                type: 'variation',
                featureInfoPlugin: function ( f, info ) {
                    if ( f.id ) {
                        info.add( 'SNP', makeElement( 'a', f.id, {
                            href: 'http://www.ensembl.org/Homo_sapiens/Variation/Summary?v=' + f.id,
                            target: '_newtab'
                        } ) );
                    }
                }
            }, {
                name: 'Conservation',
                bwgURI: 'http://www.biodalliance.org/datasets/phastCons46way.bw',
                noDownsample: true
            }, ],

            noOptions: true,
            noTrackAdder: true,
            noTrackEditor: true,
            noExport: true,
            noLeapButtons: true
        } );

    }

    setAllele( allele ) {
        this.allele = allele;
    }

    setLocation( allele ) {
        this.browser.setLocation( allele.chromosome,
            allele.startPosition - 49,
            allele.openEndPosition + 50
        );
    }

}

GenomeBrowserWidgetVM.$inject = [ '$scope' ];
