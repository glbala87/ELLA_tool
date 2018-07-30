import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
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
    'p_denovo',
    'needs_verification'
]

function extractGenotypeDataSample(display, sample) {
    const data = {}
    if (sample.sample_type !== 'HTS') {
        return data
    }
    for (let key of GENOTYPE_KEYS) {
        if (key in sample.genotype) {
            data[key] = sample.genotype[key]
        }
    }
    data.display = display
    data.title = sample.identifier
    return data
}

const displaySamples = Compute(state`${props`allelePath`}`, (allele) => {
    const displaySamples = []
    if (!allele) {
        return displaySamples
    }
    if (allele.samples) {
        for (const sample of allele.samples) {
            let display_sex = ''
            if (sample.sex) {
                display_sex = ` (${sample.sex})`
            }
            displaySamples.push(extractGenotypeDataSample(`Proband${display_sex}`, sample))
            if (sample.father) {
                displaySamples.push(extractGenotypeDataSample('Father', sample.father))
            }
            if (sample.mother) {
                displaySamples.push(extractGenotypeDataSample('Mother', sample.mother))
            }
            if (sample.siblings) {
                for (const sibling of sample.siblings) {
                    displaySamples.push(
                        extractGenotypeDataSample(`Sibling (${siblings.sex})`, sibling)
                    )
                }
            }
        }
    }
    return displaySamples
})

app.component('alleleInfoQuality', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoQuality.ngtmpl.html',
    controller: connect(
        {
            displaySamples,
            allele: state`${props`allelePath`}`
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
