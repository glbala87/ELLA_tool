import processAlleles from '../../../../common/helpers/processAlleles'
import processAnalyses from '../../../../common/helpers/processAnalyses'
import processOverviewActivities from '../../../../common/helpers/processOverviewActivities'

export default function getOverviewActivities({ http, path, state }) {
    return http
        .get('overviews/activities/')
        .then((response) => {
            let data = response.result

            for (let d of data) {
                if ('allele' in d) {
                    processAlleles([d.allele], d.genepanel)
                }
                if ('analysis' in d) {
                    processAnalyses([d.analysis])
                }
            }

            // Must be run after processAlleles/processAnalyses
            processOverviewActivities(data, state.get('app.user'))
            return path.success(response)
        })
        .catch((response) => {
            return path.error(response)
        })
}
