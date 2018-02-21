/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import { compute } from 'cerebral'
import getGenepanelValuesForAllele from '../store/common/computes/getGenepanelValuesForAllele'

app.component('allelebar', {
    templateUrl: 'ngtmpl/allelebar-new.ngtmpl.html',
    bindings: {
        allelePath: '<',
        genepanelPath: '<'
    },
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            genepanel: state`${props`genepanelPath`}`,
            genepanelValuesForAllele: getGenepanelValuesForAllele(
                state`${props`genepanelPath`}`,
                state`${props`allelePath`}`
            )
        },
        'AlleleBar',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getGenepanelValues: symbol => $ctrl.genepanelValuesForAllele[symbol],
                    formatCodons: codons => {
                        if (codons === undefined) return

                        let shortCodon = (match, c) => {
                            if (c.length > 10) return `(${c.length})`
                            else return c
                        }

                        return codons
                            .split('/')
                            .map(c => {
                                return c.replace(/([ACGT]+)/, shortCodon)
                            })
                            .join('/')
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allelebar-old',
    scope: {
        allele: '=',
        genepanel: '=?'
    },
    templateUrl: 'ngtmpl/allelebar.ngtmpl.html'
})
@Inject('Config')
export class Allelebar {
    constructor(Config) {
        this.config = Config.getConfig()
    }

    getInheritanceCodes(geneSymbol) {
        return this.genepanel.getInheritanceCodes(geneSymbol)
    }

    phenotypesBy(geneSymbol) {
        return this.genepanel.phenotypesBy(geneSymbol)
    }

    getGenepanelValues(geneSymbol) {
        //  Cache calculation; assumes this card is associated with only one gene symbol
        if (!this.calculated_config && this.genepanel) {
            this.calculated_config = this.genepanel.calculateGenepanelConfig(
                geneSymbol,
                this.config.variant_criteria.genepanel_config
            )
        }
        return this.calculated_config
    }

    getGenotype() {
        return this.allele.formatGenotype()
    }

    formatCodons(codons) {
        if (codons === undefined) return

        let shortCodon = (match, c) => {
            if (c.length > 10) return `(${c.length})`
            else return c
        }

        return codons
            .split('/')
            .map(c => {
                return c.replace(/([ACGT]+)/, shortCodon)
            })
            .join('/')
    }
}
