import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import template from './evaluateReference.ngtmpl.html' // eslint-disable-line no-unused-vars
import popover from './referenceEvalHelpTextPopover.ngtmpl.html' // eslint-disable-line no-unused-vars
import abstractPopover from './abstractPopover.ngtmpl.html' // eslint-disable-line no-unused-vars
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

const STATE_BASE = 'views.workflows.modals.evaluateReference'

app.component('evaluateReference', {
    templateUrl: 'evaluateReference.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            dismissClicked: signal`${STATE_BASE}.dismissClicked`,
            reference: state`${STATE_BASE}.reference`,
            annotationSources: state`${STATE_BASE}.annotationSources`,
            referenceAssessment: state`${STATE_BASE}.referenceAssessment`,
            referenceAssessmentComment: state`${STATE_BASE}.referenceAssessment.evaluation.comment`,
            alleleGeneGroups: state`${STATE_BASE}.alleleGeneGroups`,
            referenceAssessmentCommentChanged: signal`${STATE_BASE}.referenceAssessmentCommentChanged`,
            evaluationChanged: signal`${STATE_BASE}.evaluationChanged`,
            sourcesChanged: signal`${STATE_BASE}.sourcesChanged`,
            readOnly: isReadOnly
        },
        'evaluateReference',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                $ctrl.modelReferenceAssessment = {}
                $ctrl.sources = {
                    // 'relevance' is a special case, so it has no 'elements' block like the others
                    relevance: {
                        title: 'Relevance',
                        desc: 'Is reference relevant?',
                        help: [
                            '- YES: The reference contains data on the exact variant given above AND is original ' +
                                'research (i.e. not only a reference to another article).',
                            '- INDIRECTLY: The reference does not describe the exact variant, but is still relevant ' +
                                'for the evaluation.',
                            '- NO: The reference does not describe the variant in any meaningful way or only refers ' +
                                'to other references.',
                            '- IGNORE: Choose this if you do not wish to evaluate this reference (e.g. if you have ' +
                                'enough other references for this variant).'
                        ],
                        buttons: ['Yes', 'Indirectly', 'No', 'Ignore'],
                        buttons_store: 'relevance'
                    },
                    review: {
                        title: 'Review',
                        desc: '',
                        help: [
                            'Choose this if the paper is a review with no original data. In most cases, you would ' +
                                'rather want to find the relevant original articles, but if the review adds something ' +
                                'essential, you can add it here.'
                        ],
                        optional: true
                    },
                    aa_overlap: {
                        title: 'Overlapping amino acid',
                        desc: 'Effect of amino acid change?',
                        help: [
                            'Choose this if the present variant is located in an amino acid that is decribed in the ' +
                                'paper, but where the particular nucleotide change differs.',
                            '- PATHOGENIC, VUS or BENIGN: Choose what the amino acid change is described as in the paper.',
                            '- Choose STRONG quality when the biological relevance of the assay is high,  MODERATE if ' +
                                'it is questionable, or WEAK when the quality is so low it cannot be trusted. Otherwise ' +
                                '(if you are unsure), choose UNKNOWN.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Pathogenic', 'overlap_pat'],
                                    ['VUS', 'overlap_vus'],
                                    ['Benign', 'overlap_ben']
                                ],
                                store: 'ref_aa_overlap'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'overlap_HQ'],
                                    ['Quality: Moderate', 'overlap_MQ'],
                                    ['Quality: Weak', 'overlap_WQ'],
                                    ['Quality: Unknown', 'overlap_UQ']
                                ],
                                store: 'ref_aa_overlap_quality'
                            }
                        ],
                        optional: true,
                        parent_question: true,
                        hide_when_source: 'review'
                    },
                    aa_overlap_same_novel: {
                        title: '',
                        desc: 'Changes to same or novel amino acid?',
                        help: [
                            'Choose SAME AA if the present variant results in the same amino acid change as described ' +
                                'in the paper; otherwise, choose NOVEL AA.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Same aa', 'same_aa'], ['Novel aa', 'novel_aa']],
                                store: 'ref_aa_overlap_same_novel'
                            }
                        ],
                        optional_dep: 'aa_overlap',
                        hide_when_source: 'review'
                    },
                    aa_overlap_sim: {
                        title: '',
                        desc: 'Similar amino acid properties?',
                        help: [
                            'Select the variant amino acid from the paper in the second box, the first box should be ' +
                                'prefilled with the variant amino acid in your sample. Otherwise, you may directly choose ' +
                                'whether the amino acid in the paper and in your patient has the same or different ' +
                                'biochemical properties (= PROPERTY or ≠ PROPERTY, respectively).'
                        ],
                        elements: [
                            {
                                type: 'dropdown',
                                placeholder: 'AA IN SAMPLE',
                                options: [
                                    ['Ala', 'Ala'],
                                    ['Cys', 'Cys'],
                                    ['Asp', 'Asp'],
                                    ['Glu', 'Glu'],
                                    ['Phe', 'Phe'],
                                    ['Gly', 'Gly'],
                                    ['His', 'His'],
                                    ['Ile', 'Ile'],
                                    ['Lys', 'Lys'],
                                    ['Leu', 'Leu'],
                                    ['Met', 'Met'],
                                    ['Asn', 'Asn'],
                                    ['Pro', 'Pro'],
                                    ['Gln', 'Gln'],
                                    ['Arg', 'Arg'],
                                    ['Ser', 'Ser'],
                                    ['Thr', 'Thr'],
                                    ['Val', 'Val'],
                                    ['Trp', 'Trp'],
                                    ['Tyr', 'Tyr'],
                                    ['*', '*']
                                ],
                                store: 'ref_aa_overlap_aa'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'AA IN STUDY',
                                options: [
                                    ['Ala', 'Ala'],
                                    ['Cys', 'Cys'],
                                    ['Asp', 'Asp'],
                                    ['Glu', 'Glu'],
                                    ['Phe', 'Phe'],
                                    ['Gly', 'Gly'],
                                    ['His', 'His'],
                                    ['Ile', 'Ile'],
                                    ['Lys', 'Lys'],
                                    ['Leu', 'Leu'],
                                    ['Met', 'Met'],
                                    ['Asn', 'Asn'],
                                    ['Pro', 'Pro'],
                                    ['Gln', 'Gln'],
                                    ['Arg', 'Arg'],
                                    ['Ser', 'Ser'],
                                    ['Thr', 'Thr'],
                                    ['Val', 'Val'],
                                    ['Trp', 'Trp'],
                                    ['Tyr', 'Tyr'],
                                    ['*', '*']
                                ],
                                store: 'ref_aa_overlap_aa_ref'
                            },
                            {
                                type: 'button',
                                options: [['= property', 'sim_prop'], ['≠ property', 'diff_prop']],
                                store: 'ref_aa_overlap_sim'
                            }
                        ],
                        optional_dep: 'aa_overlap',
                        hide_when_source: 'review',
                        show_when_selection: ['ref_aa_overlap_same_novel', 'novel_aa']
                    },
                    domain_overlap: {
                        title: 'Critical domain/site or hotspot',
                        desc: 'In mutational hotspot or critical functional domain/site?',
                        help: [
                            'Choose this if the present variant is located in a mutational hotspot or critical ' +
                                'domain or site that is described in the study. Choose HOTSPOT if located in a known ' +
                                'mutation hotspot, DOMAIN if the variant is located in a critical functional domain, ' +
                                'or SITE if the variant is located in a specific, critical amino acid.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Hotspot', 'mut_hotspot'],
                                    ['Domain', 'crit_domain'],
                                    ['Site', 'crit_site']
                                ],
                                store: 'ref_domain_overlap'
                            }
                        ],
                        buttons_store: 'ref_domain_overlap',
                        optional: true,
                        parent_question: true,
                        hide_when_source: 'review'
                    },
                    domain_benign: {
                        title: '',
                        desc: 'Does the domain/site/hotspot have known benign variation?',
                        help: [
                            'Choose YES if there is known benign variation in this hotspot/domain/site, otherwise ' +
                                'choose NO (equal to PM1/PSxPM1), or UNKNOWN if unsure.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Yes', 'benign_variation'],
                                    ['No', 'no_benign_variation'],
                                    ['Unknown', 'benign_variation_unknown']
                                ],
                                store: 'ref_domain_benign'
                            }
                        ],
                        optional_dep: 'domain_overlap',
                        hide_when_source: 'review'
                    },
                    repeat_overlap: {
                        title: 'Overlapping repeat region',
                        desc: 'Does the repeat have any known function?',
                        help: [
                            'Choose this if the present variant is located in a repeat region that is described in ' +
                                'the paper. Choose YES if the repeat has a known function, otherwise choose NO, or ' +
                                'UNKNOWN if the issue is not discussed.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Yes', 'repeat_funct'],
                                    ['No', 'repeat'],
                                    ['Unknown', 'repeat_unknown']
                                ],
                                store: 'ref_repeat_overlap'
                            }
                        ],
                        buttons_store: 'ref_repeat_overlap',
                        optional: true,
                        hide_when_source: 'review'
                    },
                    auth_classification: {
                        title: 'Conclusion',
                        desc: 'Author variant classification',
                        help: [
                            'The conclusion about the variant in question given by the authors of the article ' +
                                '(important: not your own classification!). If the authors have not explicitly classified ' +
                                'the variant, choose NOT CLASSIFIED.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Pathogenic', 'pathogenic'],
                                    ['VUS', 'vus'],
                                    ['Neutral', 'neutral'],
                                    ['Not classified', 'not_classified']
                                ],
                                store: 'ref_auth_classification'
                            }
                        ]
                    },
                    segregation: {
                        title: 'Family',
                        desc: 'Variant segregates with disease?',
                        help: [
                            '- YES: The variant cosegregates with disease. Required for PP1.',
                            '- NO: The variant does not segregate with disease in affected members of a family. ' +
                                'Required for BS4.',
                            '- Quality determines which strength is suggested for the PP1/BS4 codes. Choose STRONG ' +
                                'only in cases where the evidence is of exceptional high quality. In most cases, you ' +
                                'should use MODERATE when there are more than one unrelated family and WEAK when there is ' +
                                'only one family. Use UNKNOWN if cosegregation is reported, but the strength of the ' +
                                'evidence is not possible to asscertain.',
                            '- Note: quality may be calculated after Møller P. et al., 2011  (Hum  Mutat 32; 568): ' +
                                'P =1‐(1/2)n  (n = affected individuals-1) . Six meioses (e.g. two second cousins) gives ' +
                                '96.9% likelihood that the allele is disease causing, n=7 98.4%, n=8 99.2.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'segr'], ['No', 'no_segr']],
                                store: 'ref_segregation'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'segr_HQ'],
                                    ['Quality: Moderate', 'segr_MQ'],
                                    ['Quality: Weak', 'segr_WQ'],
                                    ['Quality: Unknown', 'segr_UQ']
                                ],
                                store: 'ref_segregation_quality'
                            }
                        ],
                        parent_question: true,
                        optional: true
                    },
                    de_novo: {
                        title: '',
                        desc: 'Variant confirmed/unconfirmed de novo in patient?',
                        help: [
                            '- CONFIRMED: De novo (both maternity and paternity confirmed) in a patient with the ' +
                                'disease and no family history. Equal to PS2.',
                            '- UNCONFIRMED: Assumed de novo, but without confirmation of paternity and maternity. ' +
                                'Equal to PM6.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Confirmed', 'de_novo_confirmed'],
                                    ['Unconfirmed', 'de_novo_unconfirmed']
                                ],
                                store: 'ref_de_novo'
                            }
                        ],
                        optional_dep: 'segregation'
                    },
                    phase: {
                        title: '',
                        desc: 'Variant cis/trans with pathogenic?',
                        help: [
                            '- CIS: Observed in cis with a pathogenic variant. Equal to BP2. ',
                            '- TRANS: The variant is located in trans with a pathogenic variant. Required for PM3 ' +
                                '(with AR) or BP2 (with AD).'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Cis', 'in_cis_pathogenic'],
                                    ['Trans', 'in_trans_pathogenic']
                                ],
                                store: 'ref_phase'
                            }
                        ],
                        optional_dep: 'segregation'
                    },
                    protein: {
                        title: 'Protein',
                        desc: 'Abnormal protein function?',
                        help: [
                            '- YES: Protein assays demonstrate potentially adverse effect of variant.',
                            '- NO: Protein assays were performed, but no effect demonstrated.',
                            '- Choose STRONG quality when the biological relevance of the assay is high,  MODERATE if ' +
                                'it is questionable, or WEAK when the quality is so low it cannot be trusted. Otherwise ' +
                                '(if you are unsure), choose UNKNOWN.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'prot_abnormal'], ['No', 'prot_normal']],
                                store: 'ref_prot'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'prot_HQ'],
                                    ['Quality: Moderate', 'prot_MQ'],
                                    ['Quality: Weak', 'prot_WQ'],
                                    ['Quality: Unknown', 'prot_UQ']
                                ],
                                store: 'ref_prot_quality'
                            }
                        ],
                        optional: true
                    },
                    rna: {
                        title: 'RNA',
                        desc: 'Abnormal splicing/protein expression?',
                        help: [
                            '- YES: RNA assays demonstrate that the variant has an effect on either expression or ' +
                                'splicing.',
                            '- NO: RNA assays were performed, but no effect demonstrated.',
                            '- Choose STRONG quality when the biological relevance of the assay is high,  MODERATE ' +
                                'if it is questionable, or WEAK when the quality is so low it cannot be trusted. ' +
                                'Otherwise (if you are unsure), choose UNKNOWN.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'rna_abnormal'], ['No', 'rna_normal']],
                                store: 'ref_rna'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'rna_HQ'],
                                    ['Quality: Moderate', 'rna_MQ'],
                                    ['Quality: Weak', 'rna_WQ'],
                                    ['Quality: Unknown', 'rna_UQ']
                                ],
                                store: 'ref_rna_quality'
                            }
                        ],
                        optional: true
                    },
                    msi: {
                        title: 'MSI',
                        desc: 'Instability demonstrated?',
                        help: [
                            '- YES: Assays demonstrate microsatellite instability.',
                            '- NO: Assays do not demonstrate microsatellite instability.',
                            '- STRONG quality: >=2 tumors with MSI OR ≥3 tumors without MSI; MODERATE quality: 1 tumor ' +
                                'with MSI OR 1 or 2 tumors without MSI; WEAK quality: when the evidence cannot be trusted. ' +
                                'Otherwise (if you are unsure), choose UNKNOWN.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'msi'], ['No', 'no_msi']],
                                store: 'ref_msi'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'msi_HQ'],
                                    ['Quality: Moderate', 'msi_MQ'],
                                    ['Quality: Weak', 'msi_WQ'],
                                    ['Quality: Unknown', 'msi_UQ']
                                ],
                                store: 'ref_msi_quality'
                            }
                        ],
                        optional: true,
                        gene_group_only: 'MMR'
                    },
                    ihc: {
                        title: 'IHC',
                        desc: 'Loss of MMR protein?',
                        help: [
                            '- YES: IHC demonstrates loss of MMR protein in tumor tissue.',
                            '- NO: IHC does not demonstrate loss of MMR protein in tumor tissue, in one or more ' +
                                'tumors. Equal to BS3.',
                            '- STRONG quality: >=2 tumors with loss of MMR protein; MODERATE quality: 1 tumor with ' +
                                'loss of MMR protein; WEAK quality: when the evidence cannot be trusted. Otherwise (if ' +
                                'you are unsure), choose UNKNOWN.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'mmr_loss'], ['No', 'mmr_noloss']],
                                store: 'ref_ihc'
                            },
                            {
                                type: 'dropdown',
                                placeholder: 'CHOOSE QUALITY',
                                options: [
                                    ['Quality: Strong', 'ihc_HQ'],
                                    ['Quality: Moderate', 'ihc_MQ'],
                                    ['Quality: Weak', 'ihc_WQ'],
                                    ['Quality: Unknown', 'ihc_UQ']
                                ],
                                store: 'ref_ihc_quality',
                                when_selection: ['ref_ihc', 'mmr_loss']
                            }
                        ],
                        optional: true,
                        gene_group_only: 'MMR'
                    },
                    prediction: {
                        title: 'In silico',
                        desc: 'Results of prediction tools?',
                        help: ["If unsure about the results, use the authors' definition."],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Pathogenic', 'pat'],
                                    ['VUS', 'vus'],
                                    ['Neutral', 'neu']
                                ],
                                store: 'ref_prediction'
                            },
                            {
                                type: 'text',
                                placeholder: 'Enter tools...',
                                store: 'ref_prediction_tool'
                            }
                        ],
                        optional: true
                    },
                    population_affecteds: {
                        title: 'Population',
                        desc: 'Observed in UNRELATED affecteds?',
                        help: [
                            'Observed in the chosen number of patients unrelated to your own, and not in controls.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['>=4 affected', 'in_many_aff'],
                                    ['3 affected', 'in_more_aff'],
                                    ['1-2 affected', 'in_few_aff']
                                ],
                                store: 'ref_population_affecteds'
                            }
                        ],
                        parent_question: true,
                        optional: true
                    },
                    population_healthy: {
                        title: '',
                        desc: 'Observed in healthy individual/population?',
                        help: [
                            '- YES: Observed in at least one well-documented healthy adult for a recessive ' +
                                '(homozygous), dominant (heterozygous), or X-linked (hemizygous) disorder. Equal to BS2.',
                            '- NO: Not observed in a healthy population (as reported  in the study).'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [['Yes', 'in_healthy'], ['No', 'null_freq']],
                                store: 'ref_population_healthy'
                            }
                        ],
                        optional_dep: 'population_affecteds'
                    },
                    quality: {
                        title: 'Overall quality',
                        desc: '',
                        help: [
                            'Your own overall evaluation of the quality of the evidence you have included in this ' +
                                'form. This can be used as a guide for the next interpreter when choosing between multiple ' +
                                'references for the same variant, if present.'
                        ],
                        elements: [
                            {
                                type: 'button',
                                options: [
                                    ['Excellent', 'excellent'],
                                    ['Good', 'good'],
                                    ['Passable', 'passable'],
                                    ['Lacking', 'lacking'],
                                    ['Poor', 'poor']
                                ],
                                store: 'ref_quality'
                            }
                        ]
                    }
                }

                $ctrl.relevance_show = {
                    Yes: [
                        'auth_classification',
                        'segregation',
                        'de_novo',
                        'phase',
                        'population_affecteds',
                        'population_healthy',
                        'protein',
                        'rna',
                        'msi',
                        'ihc',
                        'prediction',
                        'quality'
                    ],
                    Indirectly: [
                        'review',
                        'aa_overlap',
                        'aa_overlap_same_novel',
                        'aa_overlap_sim',
                        'domain_overlap',
                        'domain_benign',
                        'repeat_overlap',
                        'quality'
                    ],
                    No: [],
                    Ignore: []
                }
                Object.assign($ctrl, {
                    shouldShow: (source) => {
                        let should_show = true

                        if ('gene_group_only' in $ctrl.sources[source]) {
                            return $ctrl.alleleGeneGroups.includes(
                                $ctrl.sources[source].gene_group_only
                            )
                        }

                        if ('hide_when_source' in $ctrl.sources[source]) {
                            should_show = !$ctrl.referenceAssessment.evaluation.sources.includes(
                                $ctrl.sources[source].hide_when_source
                            )
                        }

                        if ('show_when_selection' in $ctrl.sources[source]) {
                            if (!should_show) {
                                return false
                            }
                            return (
                                $ctrl.referenceAssessment.evaluation[
                                    $ctrl.sources[source].show_when_selection[0]
                                ] === $ctrl.sources[source].show_when_selection[1]
                            )
                        } else {
                            return should_show
                        }
                    },
                    /**
                     * Returns the sources to list as options
                     */
                    getSources: () => {
                        return $ctrl.relevance_show[$ctrl.referenceAssessment.evaluation.relevance]
                    },

                    isDisabled: (source) => {
                        let optional = false
                        if ('optional' in $ctrl.sources[source]) {
                            optional = $ctrl.sources[source].optional
                            if (!optional) {
                                return false
                            }
                        }

                        if ('optional_dep' in $ctrl.sources[source]) {
                            source = $ctrl.sources[source].optional_dep
                            optional = true
                        }
                        if (optional) {
                            return (
                                $ctrl.referenceAssessment.evaluation.sources.find(
                                    (e) => e === source
                                ) === undefined
                            )
                        } else {
                            return false
                        }
                    },
                    sourceSelected: (source) => {
                        return $ctrl.referenceAssessment.evaluation.sources.includes(source)
                    },
                    /**
                     * Cleans up the evaluation, removing all data that is not
                     * selected or not shown in the UI.
                     * Reason is to not store any user selection that is no more
                     * relevant.
                     */
                    close: () => {
                        for (let [source, source_data] of Object.entries($ctrl.sources)) {
                            // relevance is special
                            if (source === 'relevance') {
                                continue
                            }
                            // If not visible or disabled -> delete data
                            if (
                                !$ctrl.getSources().includes(source) ||
                                $ctrl.isDisabled(source) ||
                                ($ctrl.getSources().includes(source) && !$ctrl.shouldShow(source))
                            ) {
                                // Clean up evaluation
                                if ('elements' in source_data) {
                                    for (let elem of source_data.elements) {
                                        delete $ctrl.referenceAssessment.evaluation[elem.store]
                                    }
                                }

                                // Clean up enabled sources
                                let idx = $ctrl.referenceAssessment.evaluation.sources.findIndex(
                                    (e) => e === source
                                )
                                if (idx >= 0) {
                                    $ctrl.referenceAssessment.evaluation.sources.splice(idx, 1)
                                }
                            }
                        }
                        return $ctrl.dismissClicked({
                            evaluation: $ctrl.referenceAssessment.evaluation
                        })
                    }
                })
            }
        ]
    )
})
