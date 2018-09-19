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
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import { formatFreqValue } from '../store/common/computes/getFrequencyAnnotation'
import template from './alleleSidebarList.ngtmpl.html'
import qualityPopoverTemplate from '../widgets/allelesidebar/alleleSidebarQualityPopover.ngtmpl.html'
import frequencyPopoverTemplate from '../widgets/allelesidebar/alleleSidebarFrequencyPopover.ngtmpl.html'
import externalPopoverTemplate from '../widgets/allelesidebar/alleleSidebarExternalPopover.ngtmpl.html'

const sectionAlleles = Compute(
    props`section`,
    state`views.workflows.alleleSidebar`,
    state`views.workflows.data.alleles`,
    (section, alleleSidebar, alleles) => {
        if (!section || !alleleSidebar || !alleles) {
            return
        }
        if (!(section in alleleSidebar)) {
            throw Error(`Section ${section} not present`)
        }
        return alleleSidebar[section].map((aId) => alleles[aId])
    }
)

const sectionOrderBy = Compute(
    props`section`,
    state`views.workflows.alleleSidebar.orderBy`,
    (section, orderBy) => {
        if (!section || !orderBy) {
            return
        }
        return orderBy[section]
    }
)

const isTogglable = Compute(
    state`views.workflows.data.alleles`,
    getClassification,
    state`views.workflows.selectedComponent`,
    (alleles, classifications, selectedComponent, get) => {
        const result = {}
        if (!alleles) {
            return result
        }
        const verificationStatus = get(getVerificationStatus)
        for (let [alleleId, allele] of Object.entries(alleles)) {
            if (selectedComponent !== 'Report') {
                result[alleleId] = false
                continue
            }
            result[alleleId] =
                Boolean(classifications[alleleId]) && verificationStatus[alleleId] != 'technical'
        }
        return result
    }
)

const isToggled = Compute(
    state`views.workflows.data.alleles`,
    state`views.workflows.selectedComponent`,
    (alleles, selectedComponent, get) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (let [alleleId, allele] of Object.entries(alleles)) {
            if (selectedComponent !== 'Report') {
                result[alleleId] = false
                continue
            }
            const alleleState = get(getAlleleState(alleleId))
            result[alleleId] = alleleState.report.included
        }
        return result
    }
)

app.component('alleleSidebarList', {
    bindings: {
        sectionTitle: '@',
        section: '=',
        expanded: '=',
        allowQuickClassification: '=?'
    },
    templateUrl: 'alleleSidebarList.ngtmpl.html',
    controller: connect(
        {
            selectedComponent: state`views.workflows.selectedComponent`,
            alleles: sectionAlleles,
            classification: getClassification,
            consequence: getConsequence,
            config: state`app.config`,
            isMultipleInGene,
            depth: getDepth,
            alleleassessments: getAlleleAssessments,
            alleleRatio: getAlleleRatio,
            hiFreq: getHiFrequency('freq'),
            hiCount: getHiFrequency('count'),
            externalSummary: getExternalSummary,
            readOnly: isReadOnly,
            isNonsense,
            isTogglable,
            isToggled,
            isMultipleSampleType,
            verificationStatus: getVerificationStatus,
            orderBy: sectionOrderBy,
            selectedAllele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            selectedAlleleChanged: signal`views.workflows.alleleSidebar.selectedAlleleChanged`,
            includeReportToggled: signal`views.workflows.alleleSidebar.includeReportToggled`,
            orderByChanged: signal`views.workflows.alleleSidebar.orderByChanged`,
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
                Object.assign($ctrl, {
                    rowClicked(alleleId) {
                        // Handle whether to change selected allele, or to include in report
                        if ($ctrl.selectedComponent !== 'Report') {
                            $ctrl.selectedAlleleChanged({ alleleId })
                        } else {
                            if ($ctrl.section == 'classified' && !$ctrl.isTechnical(alleleId)) {
                                $ctrl.includeReportToggled({ alleleId })
                            }
                        }
                    },
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
                        return allele.annotation.filtered
                            .map((t) => (t.symbol ? t.symbol : '-'))
                            .join(' | ')
                    },
                    getHGVSc(allele) {
                        return allele.annotation.filtered
                            .map((t) => (t.HGVSc_short ? t.HGVSc_short : allele.formatted.hgvsg))
                            .join(' | ')
                    },
                    isTechnical(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'technical'
                    },
                    isVerified(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'verified'
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
                    getQualityTitle(allele) {
                        if ($ctrl.isTechnical(allele)) {
                            return 'Technical'
                        } else if ($ctrl.isVerified(allele)) {
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
