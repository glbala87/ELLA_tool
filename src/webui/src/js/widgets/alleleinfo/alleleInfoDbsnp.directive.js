/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleInfoDbsnp', {
    templateUrl: 'ngtmpl/alleleInfoDbsnp-new.ngtmpl.html',
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
                            t => 'dbsnp' in t && t.dbsnp.length
                        )
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allele-info-dbsnp-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoDbsnp.ngtmpl.html'
})
@Inject()
export class AlleleInfoDbsnp {
    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true
        }
    }

    getUrl(dbsnp) {
        return `http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${dbsnp}`
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'dbsnp' in t && t.dbsnp.length)
    }
}
