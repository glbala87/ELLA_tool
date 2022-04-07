const FIELDS = [
    'classificationAnalysisSpecific',
    'classificationEvaluation',
    'classificationAcmg',
    'classificationReport',
    'classificationFrequency',
    'classificationPrediction',
    'classificationExternal',
    'classificationReferences',
    'geneInformation',
    'reportIndications',
    'reportSummary',
    'referenceEvaluation',
    'workLogMessage'
]

export default function setCommentTemplates({ state }) {
    const userConfig = state.get('app.config.user.user_config')
    if (
        !userConfig ||
        !('comment_templates' in userConfig) ||
        userConfig.comment_templates === null
    ) {
        state.set('app.commentTemplates', [])
        return
    }

    const templates = {}
    for (const field of FIELDS) {
        const fieldTemplates = []
        try {
            for (const candidate of userConfig.comment_templates) {
                if (candidate.comment_fields.includes(field)) {
                    fieldTemplates.push(candidate)
                }
            }
        } catch (err) {
            console.error(
                'Error while retrieving templates from:',
                userConfig.comment_templates,
                err
            )
        }
        templates[field] = fieldTemplates
    }
    state.set('app.commentTemplates', templates)
}
