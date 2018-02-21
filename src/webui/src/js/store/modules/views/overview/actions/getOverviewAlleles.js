import processAlleles from '../../../../common/helpers/processAlleles'

function getOverviewAlleles({ state, http, path }) {
    return http
        .get('overviews/alleles/')
        .then(response => {
            let data = response.result
            for (let key of ['marked_review', 'missing_alleleassessment', 'ongoing']) {
                for (let item of data[key]) {
                    processAlleles([item.allele], item.genepanel)
                }
            }

            response.result.ongoing_user = response.result.ongoing.filter(item => {
                return (
                    item.interpretations[item.interpretations.length - 1].user_id ===
                    state.get('app.user.id')
                )
            })

            response.result.ongoing_others = response.result.ongoing.filter(item => {
                return (
                    item.interpretations[item.interpretations.length - 1].user_id !==
                    state.get('app.user.id')
                )
            })

            return path.success(response)
        })
        .catch(response => {
            return path.error(response)
        })
}

export default getOverviewAlleles
