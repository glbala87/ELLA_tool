import processAnalyses from '../../../../common/helpers/processAnalyses'

const SECTIONS = [
    'not_ready',
    'not_started_all_classified',
    'not_started_missing_alleleassessments',
    'ongoing',
    'marked_review_all_classified',
    'marked_review_missing_alleleassessments',
    'marked_medicalreview'
]

export default function getOverviewAnalysesByFindings({ http, path, state }) {
    return http
        .get('overviews/analyses/by-findings/')
        .then((response) => {
            for (let section of SECTIONS) {
                for (let item of response.result[section]) {
                    processAnalyses([item])
                }
            }

            response.result.ongoing_user = response.result.ongoing.filter((item) => {
                return (
                    item.interpretations[item.interpretations.length - 1].user_id ===
                    state.get('app.user.id')
                )
            })

            response.result.ongoing_others = response.result.ongoing.filter((item) => {
                return (
                    item.interpretations[item.interpretations.length - 1].user_id !==
                    state.get('app.user.id')
                )
            })

            delete response.result.ongoing
            return path.success(response)
        })
        .catch((response) => {
            console.error(response)
            return path.error(response)
        })
}
