import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './alleleInfoQuality.ngtmpl.html'

const GENOTYPE_KEYS = [
    'multiallelic',
    'variant_quality',
    'filter_status',
    'genotype_quality',
    'genotype_likelihood',
    'sequencing_depth',
    'allele_depth',
    'allele_ratio',
    'type',
    'formatted',
    'needs_verification'
]

function extractGenotypeDataSample(display, sample) {
    const data = {}
    if (sample.sample_type !== 'HTS') {
        return data
    }
    for (let key of GENOTYPE_KEYS) {
        data[key] = sample.genotype[key]
    }
    data.display = display
    data.title = sample.identifier
    return data
}

const displaySamples = Compute(
    state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
    (allele) => {
        const displaySamples = []
        if (!allele) {
            return samples
        }
        if (allele.samples) {
            for (const sample of allele.samples) {
                displaySamples.push(extractGenotypeDataSample('Proband', sample))
                if (sample.father) {
                    displaySamples.push(extractGenotypeDataSample('Father', sample.father))
                }
                if (sample.mother) {
                    displaySamples.push(extractGenotypeDataSample('Mother', sample.mother))
                }
                if (sample.siblings) {
                    for (const sibling of sample.siblings) {
                        displaySamples.push(extractGenotypeDataSample('Sibling', sibling))
                    }
                }
            }
        }
        return displaySamples
    }
)

app.component('alleleInfoQuality', {
    templateUrl: 'alleleInfoQuality.ngtmpl.html',
    controller: connect(
        {
            displaySamples,
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoQuality',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    formatSequence: (sequence) => {
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
