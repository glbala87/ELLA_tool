import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getGenepanelValues from '../store/common/computes/getGenepanelValues'

import template from './allelebar.ngtmpl.html' // eslint-disable-line no-unused-vars
import genePopover from './allelebar/genePopover.ngtmpl.html'
import cdnaPopover from './allelebar/cdnaPopover.ngtmpl.html'
import proteinPopover from './allelebar/proteinPopover.ngtmpl.html'

const GENOTYPE_DISPLAY_MAX_CHAR = 15

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
            genepanelValues: getGenepanelValues(state`${props`genepanelPath`}`),
            genotypeDisplay
        },
        'AlleleBar',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
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
                    },
                    hasGeneAssessment(hgnc_id) {
                        return $ctrl.genepanel.geneassessments
                            .filter((ga) => ga.gene_id === hgnc_id)
                            .filter((ga) => ga.evaluation && ga.evaluation.comment).length
                    },
                    getHGVSTitle(allele) {
                        if (allele && allele.caller_type == 'SNV') {
                            return 'HGVSc:'
                        } else if (allele && allele.caller_type == 'CNV') {
                            return 'HGVSg:'
                        } else {
                            return ''
                        }
                    }
                })
            }
        ]
    )
})
