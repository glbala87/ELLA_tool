import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './similarAllelesList.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('similarAllelesList', {
    templateUrl: 'similarAllelesList.ngtmpl.html',
    controller: connect(
        {
            similar_alleles: state`views.workflows.interpretation.data.similar.${state`views.workflows.selectedAllele`}`, //TODO: only relevant data
            all_similar_alleles: state`views.workflows.interpretation.data.similar`,
            selectedAllele: state`views.workflows.selectedAllele`
        },
        'SimilarAllelesList',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getGene(allele) {
                        if (allele.annotation.filtered.length) {
                            return allele.annotation.filtered
                                .map((t) => (t.symbol ? t.symbol : '-'))
                                .join(' | ')
                        }
                        return 'chr' + allele.chromosome
                    },
                    getHGVSc(allele) {
                        if (allele.annotation.filtered.length) {
                            return allele.annotation.filtered
                                .map((t) =>
                                    t.HGVSc_short ? t.HGVSc_short : allele.formatted.hgvsg
                                )
                                .join(' | ')
                        }
                        return allele.formatted.hgvsg
                    },
                    getHGVSp(allele) {
                        if (allele.annotation.filtered.length) {
                            return allele.annotation.filtered
                                .map((t) => (t.HGVSp ? t.HGVSp : 'TODO FIXME'))
                                .join(' | ')
                        }
                        return 'TODO FIXME'
                    },
                    getClassificationText(allele) {
                        if ('allele_assessment' in allele) {
                            return `CLASS ${allele.allele_assessment.classification}`
                        }
                        return 'NEW'
                    }
                })
            }
        ]
    )
})
