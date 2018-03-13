/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import { AlleleStateHelper } from '../model/allelestatehelper'
import { deepCopy } from '../util'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isMultipleInGene from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleInGene'
import isSelected from '../store/modules/views/workflows/alleleSidebar/computed/isSelected'
import isHomozygous from '../store/modules/views/workflows/alleleSidebar/computed/isHomozygous'
import isNonsense from '../store/modules/views/workflows/alleleSidebar/computed/isNonsense'
import isLowQual from '../store/modules/views/workflows/alleleSidebar/computed/isLowQual'
import isImportantSource from '../store/modules/views/workflows/alleleSidebar/computed/isImportantSource'
import isMultipleSampleType from '../store/modules/views/workflows/alleleSidebar/computed/isMultipleSampleType'
import getConsequence from '../store/modules/views/workflows/alleleSidebar/computed/getConsequence'
import getClassification from '../store/modules/views/workflows/alleleSidebar/computed/getClassification'
import getAlleleState from '../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getVerificationStatus from '../store/modules/views/workflows/interpretation/computed/getVerificationStatus'

const unclassifiedAlleles = Compute(
    state`views.workflows.alleleSidebar.unclassified`,
    state`views.workflows.data.alleles`,
    (unclassified, alleles) => {
        return unclassified.map(aId => alleles[aId])
    }
)

const classifiedAlleles = Compute(
    state`views.workflows.alleleSidebar.classified`,
    state`views.workflows.data.alleles`,
    (classified, alleles) => {
        return classified.map(aId => alleles[aId])
    }
)

const isTogglable = Compute(
    state`views.workflows.data.alleles`,
    getClassification,
    state`views.workflows.selectedComponent`,
    (alleles, classifications, selectedComponent, get) => {
        const result = {}
        for (let [alleleId, allele] of Object.entries(alleles)) {
            if (selectedComponent !== 'Report') {
                result[alleleId] = false
                continue
            }
            result[alleleId] = Boolean(classifications[alleleId]) // FIXME: Check verification status
        }
        return result
    }
)

const isToggled = Compute(
    state`views.workflows.data.alleles`,
    state`views.workflows.selectedComponent`,
    (alleles, selectedComponent, get) => {
        const result = {}
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

app.component('alleleSidebar', {
    templateUrl: 'ngtmpl/alleleSidebar-new.ngtmpl.html',
    controller: connect(
        {
            selectedComponent: state`views.workflows.selectedComponent`,
            classified: classifiedAlleles,
            classification: getClassification,
            consequence: getConsequence,
            isHomozygous,
            isImportantSource,
            isMultipleInGene,
            isLowQual,
            isNonsense,
            isTogglable,
            isToggled,
            verificationStatus: getVerificationStatus,
            orderBy: state`views.workflows.alleleSidebar.orderBy`,
            selectedAllele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            unclassified: unclassifiedAlleles,
            selectedAlleleChanged: signal`views.workflows.alleleSidebar.selectedAlleleChanged`,
            includeReportToggled: signal`views.workflows.alleleSidebar.includeReportToggled`,
            orderByChanged: signal`views.workflows.alleleSidebar.orderByChanged`
        },
        'AlleleSidebar',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    rowClicked(alleleId, section) {
                        // Handle whether to change selected allele, or to include in report
                        if ($ctrl.selectedComponent !== 'Report') {
                            $ctrl.selectedAlleleChanged({ alleleId })
                        } else {
                            if (section == 'classified') {
                                $ctrl.includeReportToggled({ alleleId })
                            }
                        }
                    },
                    getSampleType(allele) {
                        return allele.samples
                            .map(s => s.sample_type.substring(0, 1))
                            .join('')
                            .toUpperCase()
                    },
                    getSampleTypesFull(allele) {
                        return allele.samples
                            .map(s => s.sample_type)
                            .join(', ')
                            .toUpperCase()
                    },
                    isTechnical(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'technical'
                    },
                    isVerified(allele_id) {
                        return $ctrl.verificationStatus[allele_id] === 'verified'
                    },
                    hasQualityInformation(allele_id) {
                        return (
                            $ctrl.isLowQual[allele_id] ||
                            $ctrl.isTechnical(allele_id) ||
                            $ctrl.isVerified(allele_id)
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
                    getQualityTag(allele_id) {
                        if ($ctrl.isTechnical(allele_id)) {
                            return 'T'
                        } else if ($ctrl.isVerified(allele_id)) {
                            return 'V'
                        } else if ($ctrl.isLowQual[allele_id]) {
                            return 'Q'
                        }
                    },

                    getQualityTextPopover(allele) {
                        if ($ctrl.isTechnical(allele)) {
                            return 'Technical'
                        } else if ($ctrl.isVerified(allele)) {
                            return 'Verified'
                        } else {
                            return 'Quality issues'
                        }
                    }
                })
            }
        ]
    )
})

@Directive({
    selector: 'allele-sidebar-old',
    templateUrl: 'ngtmpl/alleleSidebar.ngtmpl.html',
    scope: {
        genepanel: '=',
        alleles: '=', // Allele options: { unclassified: [ {allele: Allele, alleleState: {...}, checkable: true, checked: true ] }, classified: [ ... ] }
        selected: '=', // Selected Allele
        readOnly: '=?' // if readOnly the allele can't be added to report
    }
})
@Inject('$scope', 'orderByFilter', 'Config')
export class AlleleSidebarController {
    constructor($scope, orderByFilter, Config) {
        this.config = Config.getConfig()

        this.orderBy = {
            classified: [undefined, false],
            unclassified: [undefined, false]
        }

        this.orderByFilter = orderByFilter

        $scope.$watch(
            () => this.alleles,
            () => {
                this.classified_alleles = this.orderByFilter(
                    this.alleles.classified,
                    allele => {
                        return this.sort(allele, this.orderBy.classified[0])
                    },
                    this.orderBy.classified[1]
                )
                this.unclassified_alleles = this.orderByFilter(
                    this.alleles.unclassified,
                    allele => {
                        return this.sort(allele, this.orderBy.unclassified[0])
                    },
                    this.orderBy.unclassified[1]
                )
            }
        )
    }

    sort(allele_obj, orderBy) {
        let allele = allele_obj.allele
        switch (orderBy) {
            case 'inheritance':
                return this.getInheritance(allele)
            case 'gene':
                return allele.annotation.filtered[0].symbol
            case 'hgvsc':
                let s = allele.annotation.filtered[0].HGVSc_short || allele.getHGVSgShort()
                let d = parseInt(s.match(/[cg]\.(\d+)/)[1])
                return d
            case 'consequence':
                let consequence_priority = this.config.transcripts.consequences
                let consequences = allele.annotation.filtered.map(t => t.consequences)
                consequences = [].concat.apply([], consequences)
                let consequence_indices = consequences.map(c => consequence_priority.indexOf(c))
                return Math.min(...consequence_indices)
            case 'homozygous':
                return !this.isHomozygous(allele)
            case 'quality':
                if (this.isVerified(allele_obj.alleleState)) {
                    return 0
                } else if (this.isTechnical(allele_obj.alleleState)) {
                    return 3
                } else if (this.isLowQual(allele)) {
                    return 2
                } else {
                    return 1
                }
            case 'references':
                return !this.isImportantSource(allele)
            case '3hetAR':
                return !this.is3hetAR(allele)
            default:
                return 0
        }
    }

    sortBy(alleles_selection, sortBy) {
        // Sort alleles_selection (classified/unclassified) by sortBy
        if (this.orderBy[alleles_selection][0] === sortBy) {
            if (!this.orderBy[alleles_selection][1]) {
                this.orderBy[alleles_selection][1] = true
            } else {
                this.orderBy[alleles_selection] = [undefined, false]
            }
        } else {
            this.orderBy[alleles_selection][0] = sortBy
        }

        // Update filter on classified and unclassified alleles
        this.classified_alleles = this.orderByFilter(
            this.alleles.classified,
            allele => {
                return this.sort(allele, this.orderBy.classified[0])
            },
            this.orderBy.classified[1]
        )
        this.unclassified_alleles = this.orderByFilter(
            this.alleles.unclassified,
            allele => {
                return this.sort(allele, this.orderBy.unclassified[0])
            },
            this.orderBy.unclassified[1]
        )
    }

    select(allele_option) {
        // We have two modes, multiple checkable or normal radio selectiion (of single allele)

        // Multiple (if 'checkable' === true)
        if (this.isTogglable(allele_option)) {
            allele_option.toggle()
        } else {
            // Single selection
            this.selected = allele_option.allele
        }
    }

    isSelected(allele_option) {
        if (!this.selected) {
            return false
        }

        let matching = this.selected.id === allele_option.allele.id

        // If checkable is true, we don't support select mode. Set to null
        if (matching && allele_option.checkable) {
            this.selected = null
            return false
        }
        return matching
    }

    isToggled(allele_option) {
        if (this.isTogglable(allele_option)) {
            return allele_option.isToggled()
        }
        return false
    }

    isTogglable(allele_option) {
        return allele_option.togglable && !this.isTechnical(allele_option.alleleState)
    }

    getSampleType(allele) {
        return allele.samples
            .map(s => s.sample_type.substring(0, 1))
            .join('')
            .toUpperCase()
    }

    getSampleTypesFull(allele) {
        return allele.samples
            .map(s => s.sample_type)
            .join(', ')
            .toUpperCase()
    }

    getConsequence(allele) {
        let consequence_priority = this.config.transcripts.consequences
        let sort_func = (a, b) => {
            return consequence_priority.indexOf(a) - consequence_priority.indexOf(b)
        }
        return allele.annotation.filtered
            .map(t => t.consequences.sort(sort_func)[0].replace('_variant', ''))
            .join(' | ')
    }

    getInheritance(allele) {
        if (this.genepanel) {
            return this.genepanel.getDisplayInheritance(allele.annotation.filtered[0].symbol)
        }
    }

    getClassification(allele, allele_state) {
        let classification = AlleleStateHelper.getClassification(allele, allele_state)
        if (AlleleStateHelper.isAlleleAssessmentOutdated(allele, this.config)) {
            classification = `${classification}*`
        }
        if (this.isTechnical(allele_state)) {
            classification = `(${classification})`
        }
        return classification
    }

    isHomozygous(allele) {
        return allele.samples[0].genotype.homozygous
    }

    isLowQual(allele) {
        return allele.samples.some(s => s.genotype.needs_verification)
    }

    isTechnical(allele_state) {
        return allele_state.verification === 'technical'
    }

    isVerified(allele_state) {
        return allele_state.verification === 'verified'
    }

    hasQualityInformation(alleleObj) {
        return (
            this.isLowQual(alleleObj.allele) ||
            this.isTechnical(alleleObj.alleleState) ||
            this.isVerified(alleleObj.alleleState)
        )
    }

    getQualityClass(alleleObj) {
        if (this.isTechnical(alleleObj.alleleState)) {
            return 'technical'
        } else if (this.isVerified(alleleObj.alleleState)) {
            return 'verified'
        } else {
            return 'low-qual'
        }
    }

    getQualityTag(alleleObj) {
        if (this.isTechnical(alleleObj.alleleState)) {
            return 'T'
        } else if (this.isVerified(alleleObj.alleleState)) {
            return 'V'
        } else if (this.isLowQual(alleleObj.allele)) {
            return 'Q'
        }
    }

    getQualityTextPopover(alleleObj) {
        if (this.isTechnical(alleleObj.alleleState)) {
            return 'Technical'
        } else if (this.isVerified(alleleObj.alleleState)) {
            return 'Verified'
        } else {
            return 'Quality issues'
        }
    }

    isNonsense(allele) {
        let nonsense_consequences = [
            'start_lost',
            'initiator_codon_variant',
            'transcript_ablation',
            'splice_donor_variant',
            'splice_acceptor_variant',
            'stop_gained',
            'frameshift_variant'
        ]
        return allele.annotation.filtered.some(t => {
            return nonsense_consequences.some(c => {
                return t.consequences.includes(c)
            })
        })
    }

    isImportantSource(allele) {
        return 'HGMD' in allele.annotation.external && allele.annotation.external.HGMD.tag
    }

    isMultipleInAlleleGenes(allele) {
        let other_alleles = this.alleles.classified
            .concat(this.alleles.unclassified)
            .map(a => a.allele)
            .filter(
                // Exclude "ourself"
                a => a !== allele
            )
        let other_alleles_genes = []
        for (let other_allele of other_alleles) {
            other_alleles_genes.push(...other_allele.annotation.filtered.map(f => f.symbol))
        }
        let our_genes = allele.annotation.filtered.map(f => f.symbol)
        return our_genes.some(s => other_alleles_genes.includes(s))
    }

    is3hetAR(allele) {
        if (this.isHomozygous(allele)) return false
        if (this.isMultipleInAlleleGenes(allele)) return false
        if (this.isImportantSource(allele)) return false
        if (this.getInheritance(allele) !== 'AR') return false
        if (this.isNonsense(allele)) return false
        return true
    }
}
