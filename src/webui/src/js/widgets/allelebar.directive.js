import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getGenepanelValuesForAllele from '../store/common/computes/getGenepanelValuesForAllele'
import template from './allelebar.ngtmpl.html'
import phenotypesPopover from './allelebar/phenotypes_popover.ngtmpl.html'
import cdnaPopover from './allelebar/cdnaPopover.ngtmpl.html'
import proteinPopover from './allelebar/proteinPopover.ngtmpl.html'

const genotypeDisplay = Compute(state`${props`allelePath`}`, (allele) => {
    const genotypes = []
    if (allele && allele.samples) {
        for (let sample of allele.samples) {
            genotypes.push({
                sample_label: 'P',
                display: sample.genotype.formatted,
                title: `Proband: ${sample.genotype.formatted}`,
                type: sample.genotype.type,
                multiallelic: sample.genotype.multiallelic
            })
            if (sample.father) {
                genotypes.push({
                    sample_label: 'F',
                    display: sample.father.genotype.formatted,
                    title: `Father: ${sample.father.genotype.formatted}`,
                    type: sample.father.genotype.type,
                    multiallelic: sample.father.genotype.multiallelic
                })
            }
            if (sample.mother) {
                genotypes.push({
                    sample_label: 'M',
                    display: sample.mother.genotype.formatted,
                    title: `Mother: ${sample.mother.genotype.formatted}`,
                    type: sample.mother.genotype.type,
                    multiallelic: sample.mother.genotype.multiallelic
                })
            }
            if (sample.siblings) {
                for (const sibling of sample.siblings) {
                    genotypes.push({
                        sample_label: 'S',
                        display: sibling.genotype.formatted,
                        title: `Sibling: ${sibling.genotype.formatted}`,
                        type: sibling.genotype.type,
                        multiallelic: sibling.genotype.multiallelic
                    })
                }
            }
        }
    }
    return genotypes
})

app.component('allelebar', {
    templateUrl: 'allelebar.ngtmpl.html',
    bindings: {
        allelePath: '<',
        genepanelPath: '<'
    },
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            genepanel: state`${props`genepanelPath`}`,
            genotypeDisplay,
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
                    getGenepanelValues: (symbol) => $ctrl.genepanelValuesForAllele[symbol],
                    formatCodons: (codons) => {
                        if (codons === undefined) return

                        let shortCodon = (match, c) => {
                            if (c.length > 10) return `(${c.length})`
                            else return c
                        }

                        return codons
                            .split('/')
                            .map((c) => {
                                return c.replace(/([ACGT]+)/, shortCodon)
                            })
                            .join('/')
                    }
                })
            }
        ]
    )
})
