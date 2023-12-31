import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getGenepanelValues from '../store/common/computes/getGenepanelValues'

import template from './allelebar.ngtmpl.html' // eslint-disable-line no-unused-vars
import genePopover from './allelebar/genePopover.ngtmpl.html'
import cdnaPopover from './allelebar/cdnaPopover.ngtmpl.html'
import proteinPopover from './allelebar/proteinPopover.ngtmpl.html'
import { chrToContigRef } from '../util'

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
                    getTranscriptText(allele, transcript) {
                        if (allele && allele.caller_type == 'snv') {
                            return transcript.transcript + ':'
                        } else return ''
                    },
                    hasGeneAssessment(hgnc_id) {
                        return $ctrl.genepanel.geneassessments
                            .filter((ga) => ga.gene_id === hgnc_id)
                            .filter((ga) => ga.evaluation && ga.evaluation.comment).length
                    },
                    getHGVSTitle(allele) {
                        if (allele && allele.caller_type == 'snv') {
                            return 'HGVSc:'
                        } else if (allele && allele.caller_type == 'cnv') {
                            return 'HGVSg:'
                        } else {
                            return ''
                        }
                    },
                    getHGVSg(allele) {
                        return `${chrToContigRef(allele.chromosome)}:${allele.formatted.hgvsg}`
                    },
                    getUCSCLink() {
                        let start = $ctrl.allele.start_position - 14
                        let end = $ctrl.allele.open_end_position + 15
                        console.log(start, end)
                        if (
                            $ctrl.allele.change_type === 'dup' ||
                            $ctrl.allele.change_type === 'dup_tandem'
                        ) {
                            end = $ctrl.allele.start_position + $ctrl.allele.length + 15
                        }
                        return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${$ctrl.allele.chromosome}%3A${start}-${end}`
                    }
                })
            }
        ]
    )
})
