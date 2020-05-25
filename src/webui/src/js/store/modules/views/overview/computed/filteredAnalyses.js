import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.overview.data.analyses`,
    state`views.overview.filter`,
    (analyses, filter) => {
        if (!filter || !Object.values(filter).some((x) => x !== null && x !== '')) {
            return analyses
        }
        const filteredAnalyses = {}
        nameMatch = new RegExp(`.*${filter.analysisName}.*`, 'i')
        for (let [sectionName, sectionAnalyses] of Object.entries(analyses)) {
            filteredAnalyses[sectionName] = sectionAnalyses.filter((a) => {
                return nameMatch.test(a.name)
            })
        }
        return filteredAnalyses
    }
)
