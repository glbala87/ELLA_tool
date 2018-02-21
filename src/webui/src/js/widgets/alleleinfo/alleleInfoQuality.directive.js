/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleInfoQuality', {
    templateUrl: 'ngtmpl/alleleInfoQuality-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoQuality',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    formatSequence: sequence => {
                        if (sequence.length > 10) {
                            return `(${sequence.length})`
                        } else {
                            return sequence
                        }
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allele-info-quality-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoQuality.ngtmpl.html'
})
@Inject()
export class AlleleInfoQuality {
    constructor() {}

    getVerificationText() {
        return this.allele.annotation.quality.needs_verification ? 'Yes' : 'No'
    }

    getGenotypeForSample() {
        // TODO: Fix me when introducing multiple samples...
        return this.allele.samples[0].genotype
    }

    formatSequence(sequence) {
        if (sequence.length > 10) return `(${sequence.length})`
        else return sequence
    }
}
