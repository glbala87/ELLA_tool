import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isManuallyAddedById from '../store/modules/views/workflows/alleleSidebar/computed/isManuallyAddedById'
import isMultipleInGeneById from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleInGeneById'
import isNonsenseById from '../store/modules/views/workflows/alleleSidebar/computed/isNonsenseById'
import isMultipleSampleType from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleSampleType'
import getConsequenceById from '../store/modules/views/workflows/alleleSidebar/computed/getConsequenceById'
import getHiFrequencyById from '../store/modules/views/workflows/alleleSidebar/computed/getHiFrequencyById'
import getDepthById from '../store/modules/views/workflows/alleleSidebar/computed/getDepthById'
import getAlleleRatioById from '../store/modules/views/workflows/alleleSidebar/computed/getAlleleRatioById'
import getExternalSummaryById from '../store/modules/views/workflows/alleleSidebar/computed/getExternalSummaryById'
import getClassificationById from '../store/modules/views/workflows/alleleSidebar/computed/getClassificationById'
import getAlleleAssessmentsById from '../store/modules/views/workflows/alleleSidebar/computed/getAlleleAssessmentsById'
import getVerificationStatusById from '../store/modules/views/workflows/alleleSidebar/computed/getVerificationStatusById'
import { formatFreqValue } from '../store/common/computes/getFrequencyAnnotation'
import getAlleleStateById from '../store/modules/views/workflows/alleleSidebar/computed/getAlleleStateById'
import isReviewedById from '../store/modules/views/workflows/alleleSidebar/computed/isReviewedById'
import getWarningById from '../store/modules/views/workflows/alleleSidebar/computed/getWarningById'

// Templates
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
        commentType: '@?', // none, 'analysis' or 'evaluation'
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
            classification: getClassificationById(state`${props`allelesPath`}`),
            reviewed: isReviewedById(state`${props`allelesPath`}`),
            consequence: getConsequenceById(state`${props`allelesPath`}`),
            config: state`app.config`,
            isMultipleInGene: isMultipleInGeneById(state`${props`allelesPath`}`),
            isManuallyAddedById: isManuallyAddedById(state`${props`allelesPath`}`),
            depth: getDepthById(state`${props`allelesPath`}`),
            alleleassessments: getAlleleAssessmentsById,
            alleleStates: getAlleleStateById,
            alleleRatio: getAlleleRatioById(state`${props`allelesPath`}`),
            hiFreq: getHiFrequencyById(state`${props`allelesPath`}`, 'freq'),
            hiCount: getHiFrequencyById(state`${props`allelesPath`}`, 'count'),
            externalSummary: getExternalSummaryById(state`${props`allelesPath`}`),
            isNonsense: isNonsenseById(state`${props`allelesPath`}`),
            isMultipleSampleType,
            warnings: getWarningById(state`${props`allelesPath`}`),
            verificationStatus: getVerificationStatusById(state`${props`allelesPath`}`),
            orderBy: state`${props`orderByPath`}`,
            selectedAllele: state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`,
            rowClicked: signal`${props`rowClickedPath`}`,
            toggleClicked: signal`${props`toggleClickedPath`}`,
            orderByChanged: signal`views.workflows.alleleSidebar.orderByChanged`,
            reviewedClicked: signal`views.workflows.alleleSidebar.reviewedClicked`,
            quickClassificationClicked: signal`views.workflows.alleleSidebar.quickClassificationClicked`,
            evaluationCommentChanged: signal`views.workflows.interpretation.evaluationCommentChanged`,
            analysisCommentChanged: signal`views.workflows.interpretation.analysisCommentChanged`
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
                                .map((t) =>
                                    t.HGVSc_short ? t.HGVSc_short : allele.formatted.hgvsg
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
                    showManuallyAddedIndicator() {
                        return Object.values($ctrl.isManuallyAddedById).some((k) => k)
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
                    isManuallyAdded(allele_id) {
                        return $ctrl.isManuallyAddedById[allele_id]
                    },
                    getExistingClassificationText(allele_id) {
                        const c = $ctrl.classification[allele_id]
                        if (!c.existing) {
                            return ''
                        }
                        return !c.reused ? `${c.existing}${c.outdated ? '*' : ''}` : ''
                    },
                    getArrowClassificationText(allele_id) {
                        const c = $ctrl.classification[allele_id]
                        return c.current ? '→' : ''
                    },
                    getCurrentClassificationText(allele_id) {
                        const c = $ctrl.classification[allele_id]
                        if (c.current) {
                            return c.current
                        } else if (c.reused) {
                            return c.existing
                        }
                        return ''
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
                        // Inherited mosaicism takes precedence if tags include both types
                        if (allele.tags.includes('inherited_mosaicism')) {
                            return 'M'
                        } else if (allele.tags.includes('denovo')) {
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
                        return $ctrl.warnings[allele.id].length > 0
                    },
                    getWarningsTitle(allele) {
                        return $ctrl.warnings[allele.id].map((w) => w.warning).join('\n')
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
                    },
                    getCommentTitle() {
                        if ($ctrl.commentType === 'analysis') {
                            return 'ANALYSIS SPECIFIC'
                        }
                        if ($ctrl.commentType === 'evaluation') {
                            return 'EVALUATION'
                        }
                        return ''
                    },
                    getCommentModel(allele_id) {
                        if ($ctrl.commentType === 'analysis') {
                            return $ctrl.alleleStates[allele_id].analysis
                        }
                        if ($ctrl.commentType === 'evaluation') {
                            return $ctrl.alleleassessments[allele_id].evaluation.classification
                        }
                    },
                    commentUpdated(allele_id, comment) {
                        if ($ctrl.commentType === 'analysis') {
                            $ctrl.analysisCommentChanged({
                                alleleId: allele_id,
                                comment
                            })
                        }
                        if ($ctrl.commentType === 'evaluation') {
                            $ctrl.evaluationCommentChanged({
                                alleleId: allele_id,
                                name: 'classification',
                                comment
                            })
                        }
                    },
                    canUpdateComment(allele_id) {
                        if ($ctrl.commentType === 'evaluation') {
                            return !$ctrl.alleleStates[allele_id].alleleassessment.reuse
                        }
                        return true
                    },
                    showComment() {
                        return ['analysis', 'evaluation'].includes($ctrl.commentType)
                    }
                })
            }
        ]
    )
})
