import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isMultipleInGene from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleInGene'
import isNonsense from '../store/modules/views/workflows/alleleSidebar/computed/isNonsense'
import isMultipleSampleType from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleSampleType'
import getConsequence from '../store/modules/views/workflows/alleleSidebar/computed/getConsequence'
import getHiFrequency from '../store/modules/views/workflows/alleleSidebar/computed/getHiFrequency'
import getDepth from '../store/modules/views/workflows/alleleSidebar/computed/getDepth'
import getAlleleRatio from '../store/modules/views/workflows/alleleSidebar/computed/getAlleleRatio'
import getExternalSummary from '../store/modules/views/workflows/alleleSidebar/computed/getExternalSummary'
import getClassification from '../store/modules/views/workflows/alleleSidebar/computed/getClassification'
import getAlleleAssessments from '../store/modules/views/workflows/alleleSidebar/computed/getAlleleAssessments'
import getAlleleState from '../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getVerificationStatus from '../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import { formatFreqValue } from '../store/common/computes/getFrequencyAnnotation'
import template from './alleleSidebarList.ngtmpl.html'
import qualityPopoverTemplate from '../widgets/allelesidebar/alleleSidebarQualityPopover.ngtmpl.html'
import frequencyPopoverTemplate from '../widgets/allelesidebar/alleleSidebarFrequencyPopover.ngtmpl.html'
import externalPopoverTemplate from '../widgets/allelesidebar/alleleSidebarExternalPopover.ngtmpl.html'

const getAlleles = (alleleIds, alleles) => {
    return Compute(alleleIds, alleles, (alleleIds, alleles) => {
        if (!alleleIds || !alleles) {
            return
        }
        return alleleIds.map((aId) => alleles[aId]).filter((a) => a !== undefined)
    })
}

app.component('alleleSidebarList', {
    bindings: {
        sectionTitle: '@?',
        alleleIdsPath: '<', // path on Cerebral store
        allelesPath: '<', // path on Cerebral store
        rowClickedPath: '<',
        toggleClickedPath: '<',
        orderByPath: '<?', // path to orderBy object on Cerebral store
        expanded: '=', // bool
        readOnly: '=?', // bool
        togglable: '=?', // optional, bool, default: false
        toggled: '=?', // optional, {[id]: bool, ... }, default: false for all
        allowQuickClassification: '=?', // bool, default false
        shadeMultipleInGene: '=?' // bool, default true
    },
    templateUrl: 'alleleSidebarList.ngtmpl.html',
    controller: connect(
        {
            selectedComponent: state`views.workflows.selectedComponent`,
            alleles: getAlleles(state`${props`alleleIdsPath`}`, state`${props`allelesPath`}`),
            classification: getClassification,
            consequence: getConsequence(state`${props`allelesPath`}`),
            config: state`app.config`,
            isMultipleInGene: isMultipleInGene(state`${props`allelesPath`}`),
            depth: getDepth(state`${props`allelesPath`}`),
            alleleassessments: getAlleleAssessments,
            alleleRatio: getAlleleRatio(state`${props`allelesPath`}`),
            hiFreq: getHiFrequency(state`${props`allelesPath`}`, 'freq'),
            hiCount: getHiFrequency(state`${props`allelesPath`}`, 'count'),
            externalSummary: getExternalSummary(state`${props`allelesPath`}`),
            isNonsense: isNonsense(state`${props`allelesPath`}`),
            isMultipleSampleType,
            orderBy: state`${props`orderByPath`}`,
            verificationStatus: getVerificationStatus(state`${props`allelesPath`}`),
            selectedAllele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            rowClicked: signal`${props`rowClickedPath`}`,
            toggleClicked: signal`${props`toggleClickedPath`}`,
            orderByChanged: signal`views.workflows.alleleSidebar.orderByChanged`,
            // TODO: Consider refactoring the ones below out of this component
            quickClassificationClicked: signal`views.workflows.alleleSidebar.quickClassificationClicked`,
            evaluationCommentChanged: signal`views.workflows.interpretation.evaluationCommentChanged`,
            verificationStatusChanged: signal`views.workflows.verificationStatusChanged`
        },
        'AlleleSidebarList',
        [
            '$scope',
            function($scope) {
                const SEGREGATION_TAGS = [
                    ['denovo', 'De novo'],
                    ['compound_heterozygous', 'Compound heterozygous'],
                    ['autosomal_recessive_homozygous', 'Autosomal recessive homozygous'],
                    ['xlinked_recessive_homozygous', 'X-linked recessive']
                ]

                const $ctrl = $scope.$ctrl

                $ctrl.shadeMultipleInGene =
                    'shadeMultipleInGene' in $ctrl ? $ctrl.shadeMultipleInGene : false
                $ctrl.readOnly = 'readOnly' in $ctrl ? $ctrl.readOnly : false
                Object.assign($ctrl, {
                    getSampleType(allele) {
                        return allele.samples
                            .map((s) => s.sample_type.substring(0, 1))
                            .join('')
                            .toUpperCase()
                    },
                    getSampleTypesFull(allele) {
                        return allele.samples
                            .map((s) => s.sample_type)
                            .join(', ')
                            .toUpperCase()
                    },
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
                                .map(
                                    (t) => (t.HGVSc_short ? t.HGVSc_short : allele.formatted.hgvsg)
                                )
                                .join(' | ')
                        }
                        return allele.formatted.hgvsg
                    },
                    getHGVScTitle(allele) {
                        if (allele.annotation.filtered.length) {
                            return allele.annotation.filtered
                                .map((t) => {
                                    const transcript = t.transcript
                                    const hgvs = t.HGVSc_short
                                        ? t.HGVSc_short
                                        : allele.formatted.hgvsg
                                    return `${transcript}:${hgvs}`
                                })
                                .join(' | ')
                        }
                        return allele.formatted.hgvsg
                    },
                    isTechnical(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'technical'
                    },
                    isVerified(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'verified'
                    },
                    isTogglable() {
                        return Boolean($ctrl.togglable && !$ctrl.readOnly) || false
                    },
                    isToggled(allele_id) {
                        if (!$ctrl.toggled || !(allele_id in $ctrl.toggled)) {
                            return false
                        }
                        return $ctrl.toggled[allele_id]
                    },
                    getClassificationText(allele_id) {
                        if ($ctrl.isTechnical(allele_id)) {
                            return `(${$ctrl.classification[allele_id]})`
                        } else {
                            return $ctrl.classification[allele_id]
                        }
                    },
                    hasQualityInformation(allele) {
                        return (
                            $ctrl.isLowQual(allele) ||
                            $ctrl.isTechnical(allele.id) ||
                            $ctrl.isVerified(allele.id)
                        )
                    },
                    getQualityClass(allele_id) {
                        if ($ctrl.isTechnical(allele_id)) {
                            return 'technical'
                        } else if ($ctrl.isVerified(allele_id)) {
                            return 'verified'
                        } else {
                            return 'low-qual'
                        }
                    },
                    getQualityTag(allele) {
                        if ($ctrl.isTechnical(allele.id)) {
                            return 'T'
                        } else if ($ctrl.isVerified(allele.id)) {
                            return 'V'
                        } else if ($ctrl.isLowQual(allele)) {
                            return 'Q'
                        }
                    },
                    getQualityTitle(allele_id) {
                        if ($ctrl.isTechnical(allele_id)) {
                            return 'Technical'
                        } else if ($ctrl.isVerified(allele_id)) {
                            return 'Verified'
                        } else {
                            return 'Quality issues'
                        }
                    },
                    isLowQual(allele) {
                        return allele.tags.includes('low_quality')
                    },
                    isHomozygous(allele) {
                        return allele.tags.includes('homozygous')
                    },
                    hasReferences(allele) {
                        return allele.tags.includes('has_references')
                    },
                    getSegregationTag(allele) {
                        // Denovo takes precedence if tags include both types
                        if (allele.tags.includes('denovo')) {
                            return 'D'
                        } else if (allele.tags.includes('autosomal_recessive_homozygous')) {
                            return 'A'
                        } else if (allele.tags.includes('xlinked_recessive_homozygous')) {
                            return 'X'
                        } else if (allele.tags.includes('compound_heterozygous')) {
                            return 'C'
                        }
                    },
                    getSegregationTitle(allele) {
                        let title = []
                        for (const tag of SEGREGATION_TAGS) {
                            if (allele.tags.includes(tag[0])) {
                                title.push(tag[1])
                            }
                        }
                        return title.join('\n')
                    },
                    hasWarning(allele) {
                        return Boolean(allele.warnings)
                    },
                    getWarningsTitle(allele) {
                        if (allele.warnings) {
                            return Object.values(allele.warnings).join('\n')
                        }
                    },
                    formatFreqValue(hiFreqData) {
                        const value =
                            hiFreqData.maxMeetsThresholdValue !== null
                                ? hiFreqData.maxMeetsThresholdValue
                                : hiFreqData.maxValue
                        if (value) {
                            const formatted = formatFreqValue(value, $ctrl.config)
                            return hiFreqData.maxMeetsThresholdValue !== null
                                ? formatted
                                : `(${formatted})`
                        }
                        return '-'
                    }
                })
            }
        ]
    )
})
