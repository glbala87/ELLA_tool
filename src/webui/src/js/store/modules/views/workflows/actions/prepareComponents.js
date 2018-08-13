const BASE_SECTION_KEYS = ['classification', 'frequency', 'external', 'prediction', 'references']

const BASE_SECTIONS = {
    classification: {
        title: 'Classification',
        options: {
            hideControlsOnCollapse: false,
            showIncludedAcmgCodes: true
        },
        controls: ['classification', 'reuse_classification'],
        alleleassessmentComment: {
            placeholder: 'EVALUATION',
            name: 'classification'
        },
        reportComment: {
            placeholder: 'REPORT'
        },
        content: [{ tag: 'allele-info-acmg-selection' }, { tag: 'allele-info-classification' }]
    },
    frequency: {
        title: 'Frequency & QC',
        options: {
            hideControlsOnCollapse: true
        },
        controls: ['toggle_class2', 'validation'],
        alleleassessmentComment: {
            placeholder: 'FREQUENCY-COMMENTS',
            name: 'frequency'
        },
        content: [
            { tag: 'allele-info-frequency-gnomad-exomes' },
            { tag: 'allele-info-frequency-gnomad-genomes' },
            { tag: 'allele-info-frequency-exac' },
            { tag: 'allele-info-frequency-indb' },
            { tag: 'allele-info-dbsnp' }
        ]
    },
    external: {
        title: 'External',
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
    prediction: {
        title: 'Prediction',
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
    references: {
        title: 'Studies & References',
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
                }
            },
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Pending',
                    type: 'pending'
                }
            },
            {
                tag: 'allele-info-references',
                attr: {
                    title: 'Excluded',
                    type: 'excluded'
                }
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
                sectionKeys: BASE_SECTION_KEYS.slice()
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
                sectionKeys: BASE_SECTION_KEYS.slice()
            }
        }
    }
}

COMPONENTS.analysis.components.Classification.sections.frequency.content.push({
    tag: 'allele-info-quality'
})

function prepareComponents({ state }) {
    let components = COMPONENTS[state.get('views.workflows.type')]
    // TODO: Add IGV button to analysis frequency section
    state.set('views.workflows.components', components.components)
    state.set('views.workflows.componentKeys', components.componentKeys)
    if (state.get('views.workflows.type') === 'analysis') {
        const analysis = state.get('views.workflows.data.analysis')
        if (analysis.warnings && analysis.warnings.length) {
            state.set('views.workflows.selectedComponent', 'Info')
        } else {
            state.set('views.workflows.selectedComponent', 'Classification')
        }
    } else {
        state.set('views.workflows.selectedComponent', components.componentKeys[0])
    }
}

export default prepareComponents
