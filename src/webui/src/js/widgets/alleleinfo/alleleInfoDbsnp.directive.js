import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './alleleInfoDbsnp.ngtmpl.html'

app.component('alleleInfoDbsnp', {
    template,
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoDbsnp',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getUrl(dbsnp) {
                        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`
                    },
                    hasContent() {
                        return $ctrl.allele.annotation.filtered.some(
                            (t) => 'dbsnp' in t && t.dbsnp.length
                        )
                    }
                })
            }
        ]
    )
})
