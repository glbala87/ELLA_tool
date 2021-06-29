import { Compute } from 'cerebral'

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
        controls: ['validation', 'not-relevant']
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
        }
    },
    similar: {
        title: 'Region',
        color: 'purple',
        alleleAssessmentReusedColor: 'green',
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
        }
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
        }
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
        }
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
        }
    }
}

const CLASSIFICATION_BASE_CONTENT = {
    analysis: [{ tag: 'allele-info-quality' }],
    classification: [{ tag: 'allele-info-acmg-selection' }, { tag: 'allele-info-classification' }],
    similar: [{ tag: 'allele-info-similar-alleles' }],
    frequency: [],
    prediction: [
        { tag: 'allele-info-consequence', order: 'first' },
        { tag: 'allele-info-prediction-other', order: 'last' }
    ],
    external: [{ tag: 'allele-info-external-other', order: 'last' }],
    references: [
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
                sectionKeys: ANALYSIS_SECTION_KEYS.slice(),
                sectionContent: {}
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
                sectionKeys: ALLELE_SECTION_KEYS.slice(),
                sectionContent: {}
            }
        }
    }
}

function prepareClassificationContent(annotationConfig) {
    // const annotationViewConfig = annotationConfigs[annotationConfigIdx].view
    // Add components from the view config
    if (annotationConfig === undefined) {
        return null
    }
    const content = JSON.parse(JSON.stringify(CLASSIFICATION_BASE_CONTENT))
    for (let i in annotationConfig.view) {
        let vc = annotationConfig.view[i]
        function CamelCaseToDash(s) {
            return s.replace(/([A-Z])/g, (g) => `-${g[0].toLowerCase()}`)
        }
        const template = vc['template']
        const section = vc['section']

        content[section].push({
            tag: CamelCaseToDash(template),
            title: vc['title'],
            source: vc['source'],
            url: vc['url'],
            url_empty: vc['url_empty'],
            order: vc['order'],
            annotationConfigId: annotationConfig.id,
            annotationConfigItemIdx: parseInt(i)
        })
    }

    // Sort sectionboxes to appear in order (if defined)
    Object.values(content).forEach((x) =>
        x.sort((a, b) => {
            if (a.order === b.order) {
                return 0
            } else if (a.order === 'first' || b.order === 'last') {
                return -1
            } else if (a.order === 'last' || b.order === 'first') {
                return 1
            }
        })
    )
    return content
}

const classificationSectionContent = (alleles, annotationConfigs) => {
    return Compute(alleles, annotationConfigs, (alleles, annotationConfigs) => {
        if (!alleles) {
            return {}
        }
        const sectionContent = {}
        for (let [id, allele] of Object.entries(alleles)) {
            const annotationConfigId = allele.annotation.annotation_config_id
            const annotationConfig = annotationConfigs.find((x) => x.id === annotationConfigId)
            sectionContent[id] = prepareClassificationContent(annotationConfig)
        }

        return sectionContent
    })
}

function prepareComponents({ state, resolve }) {
    let components = COMPONENTS[state.get('views.workflows.type')]

    const annotationConfigs = state.get('views.workflows.data.annotationConfigs')
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    components.components.Classification.sectionContent = resolve.value(
        classificationSectionContent(alleles, annotationConfigs)
    )

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
export { classificationSectionContent }
