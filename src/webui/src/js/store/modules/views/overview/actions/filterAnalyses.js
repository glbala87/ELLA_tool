export default function filterAnalyses({ state }) {
    const analyses = state.get('views.overview.data.analyses')
    const filter = state.get('views.overview.filter')

    if (!filter || !Object.values(filter).some((x) => x !== null && x !== '')) {
        state.set('views.overview.filteredAnalyses', analyses)
    } else {
        const filteredAnalyses = {}
        const nameMatch = new RegExp(`.*${filter.analysisName}.*`, 'i')

        for (let [sectionName, sectionAnalyses] of Object.entries(analyses)) {
            filteredAnalyses[sectionName] = sectionAnalyses.filter((a) => {
                return (
                    (!filter.analysisName || nameMatch.test(a.name)) &&
                    (!filter.technology ||
                        (!filter.technology.Sanger && !filter.technology.HTS) ||
                        (filter.technology.Sanger && a.technology == 'Sanger') ||
                        (filter.technology.HTS && a.technology == 'HTS')) &&
                    ((!filter.priorityNormal && !filter.priorityHigh && !filter.priorityUrgent) ||
                        (filter.priorityNormal && a.priority == 1) ||
                        (filter.priorityHigh && a.priorty == 2) ||
                        (filter.priorityUrgent && a.priority == 3)) &&
                    (!filter.dateRange || withinRange(filter.dateRange, a.date_requested))
                )
            })
        }

        state.set('views.overview.filteredAnalyses', filteredAnalyses)
    }
}

function withinRange(filter, date) {
    const [amount, unit] = filter.split(':')
    // let filterDate
    // if (unit == "d") {
    //     filterDate = new Date(a.)
    // } else if (unit == "") {

    // }
    return true
}
