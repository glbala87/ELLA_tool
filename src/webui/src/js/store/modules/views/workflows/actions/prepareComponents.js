import getWarningCleared from '../worklog/computed/getWarningCleared'
const ALLELE_SECTION_KEYS = [
    'classification',
    'similar',
    'frequency',
    'prediction',
    'external',
    'references'
]
const ANALYSIS_SECTION_KEYS = [
    'analysis',
    'classification',
    'similar',
    'frequency',
    'prediction',
    'external',
    'references'
]

const BASE_SECTIONS = {
    analysis: {
        title: 'Analysis specific',
        subtitle: 'for variant',
        color: 'blue',
        options: {
            hideControlsOnCollapse: false
        },
        analysisComment: {
            placeholder: 'ANALYSIS-SPECIFIC-COMMENTS'
        },
        controls: ['validation', 'not-relevant'],
        content: [{ tag: 'allele-info-quality' }]
    },
    classification: {
        title: 'Classification',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        options: {
            hideControlsOnCollapse: false,
            showIncludedAcmgCodes: true
        },
        controls: ['classification', 'finalize', 'reuse_classification'],
        alleleassessmentComment: {
            placeholder: 'EVALUATION',
            name: 'classification'
        },
        reportComment: {
            placeholder: 'REPORT'
        },
        content: [{ tag: 'allele-info-acmg-selection' }, { tag: 'allele-info-classification' }]
    },
    similar: {
        title: 'Region',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        content: [{ tag: 'allele-info-similar-alleles' }],
        alleleassessmentComment: {
            placeholder: 'REGION-COMMENTS',
            name: 'similar'
        }
    },
    frequency: {
        title: 'Frequency',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        options: {
            hideControlsOnCollapse: true
        },
        controls: ['toggle_class2'],
        alleleassessmentComment: {
            placeholder: 'FREQUENCY-COMMENTS',
            name: 'frequency'
        },
        content: [{ tag: 'allele-info-dbsnp' }]
    },
    prediction: {
        title: 'Prediction',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        options: {
            hideControlsOnCollapse: true
        },
        controls: ['custom_prediction'],
        alleleassessmentComment: {
            placeholder: 'PREDICTION-COMMENTS',
            name: 'prediction'
        },
        content: [{ tag: 'allele-info-consequence' }, { tag: 'allele-info-prediction-other' }]
    },
    external: {
        title: 'External',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        options: {
            hideControlsOnCollapse: true
        },
        controls: ['custom_external'],
        alleleassessmentComment: {
            placeholder: 'EXTERNAL DB-COMMENTS',
            name: 'external'
        },
        content: [
            { tag: 'allele-info-hgmd' },
            { tag: 'allele-info-clinvar' },
            { tag: 'allele-info-external-other' }
        ]
    },
    references: {
        title: 'Studies & References',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
        options: {
            hideControlsOnCollapse: true
        },
        controls: ['references'],
        alleleassessmentComment: {
            placeholder: 'STUDIES-COMMENTS',
            name: 'reference'
        },
        content: [
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Evaluated',
                    type: 'evaluated'
                },
                class: ['max-width', 'reference-detail-margin-top']
            },
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Pending',
                    type: 'pending'
                },
                class: ['max-width', 'reference-detail-margin-top']
            },
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Not relevant',
                    type: 'notrelevant'
                },
                class: ['max-width', 'reference-detail-margin-top']
            },
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Ignored',
                    type: 'ignored'
                },
                class: ['max-width', 'reference-detail-margin-top']
            }
        ]
    }
}

const COMPONENTS = {
    analysis: {
        componentKeys: ['Info', 'Classification', 'Report'],
        components: {
            Info: {
                title: 'Info'
            },
            Classification: {
                title: 'Classification',
                sections: JSON.parse(JSON.stringify(BASE_SECTIONS)),
                sectionKeys: ANALYSIS_SECTION_KEYS.slice()
            },
            Report: {
                title: 'Report',
                alleles: []
            }
        }
    },
    allele: {
        componentKeys: ['Classification'],
        components: {
            Classification: {
                name: 'classification',
                title: 'Classification',
                sections: JSON.parse(JSON.stringify(BASE_SECTIONS)),
                sectionKeys: ALLELE_SECTION_KEYS.slice()
            }
        }
    }
}

function prepareComponents({ state, resolve }) {
    let components = COMPONENTS[state.get('views.workflows.type')]

    // Add components from the view config
    let annotationViewConfig = state.get('app.config.annotation.view')
    for (let i in annotationViewConfig) {
        let vc = annotationViewConfig[i]
        function CamelCaseToDash(s) {
            return s.replace(/([A-Z])/g, (g) => `-${g[0].toLowerCase()}`)
        }
        const template = vc['template']
        const section = vc['section']

        components.components.Classification.sections[section].content.push({
            tag: CamelCaseToDash(template),
            source: vc['source'],
            configIdx: i
        })
    }
    // TODO: Add IGV button to analysis frequency section
    state.set('views.workflows.components', components.components)
    state.set('views.workflows.componentKeys', components.componentKeys)
    if (state.get('views.workflows.type') === 'analysis') {
        const warningCleared = resolve.value(getWarningCleared)
        const analysis = state.get('views.workflows.data.analysis')
        if (analysis.warnings && analysis.warnings.length && !warningCleared) {
            state.set('views.workflows.selectedComponent', 'Info')
        } else {
            state.set('views.workflows.selectedComponent', 'Classification')
        }
    } else {
        state.set('views.workflows.selectedComponent', components.componentKeys[0])
    }
}

export default prepareComponents
