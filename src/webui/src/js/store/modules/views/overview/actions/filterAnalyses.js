export default function filterAnalyses({ state }) {
    const analyses = state.get('views.overview.data.analyses')
    const filter = state.get('views.overview.filter')

    if (!filter || !Object.values(filter).some((x) => x && x !== null && x !== '')) {
        state.set('views.overview.filteredAnalyses', analyses)
    } else {
        const filteredAnalyses = {}
        // allow using * as an alias for regex .+
        const nameMatch = filterToRegex(filter.analysisName)
        const commentMatch = filterToRegex(filter.reviewComment)

        for (let [sectionName, sectionAnalyses] of Object.entries(analyses)) {
            filteredAnalyses[sectionName] = sectionAnalyses.filter((a) => {
                const analysisDate = new Date(a.date_requested || a.date_deposited)
                // if there are multiple samples, check if any contain the given technology
                const analysisTechnologies = a.samples.map((s) => s.sample_type)

                return (
                    (!filter.analysisName || nameMatch.test(a.name)) &&
                    (!filter.reviewComment ||
                        (a.review_comment && commentMatch.test(a.review_comment))) &&
                    ((!filter.technologySanger && !filter.technologyHTS) ||
                        (filter.technologySanger && analysisTechnologies.includes('Sanger')) ||
                        (filter.technologyHTS && analysisTechnologies.includes('HTS'))) &&
                    ((!filter.priorityNormal && !filter.priorityHigh && !filter.priorityUrgent) ||
                        (filter.priorityNormal && a.priority === 1) ||
                        (filter.priorityHigh && a.priority === 2) ||
                        (filter.priorityUrgent && a.priority === 3)) &&
                    (!filter.dateRange || withinRange(filter.dateRange, analysisDate))
                )
            })
        }

        state.set('views.overview.filteredAnalyses', filteredAnalyses)
    }
}

function withinRange(filter, date) {
    // filter: (lt|le|gt|ge):Int:(d|m)
    const [op, amount, unit] = filter.split(':')
    let filterDate
    if (unit === 'd') {
        filterDate = createDate(Number(amount))
    } else if (unit === 'm') {
        filterDate = createDate(30 * Number(amount))
    } else {
        throw new SyntaxError(`Invalid unit in filter string: ${filter}`)
    }

    // only using lt, ge now, but might as well support others
    if (op === 'lt') {
        return filterDate < date
    } else if (op === 'le') {
        return filterDate <= date
    } else if (op === 'gt') {
        return filterDate > date
    } else if (op === 'ge') {
        return filterDate >= date
    } else {
        throw new SyntaxError(`Invalid operation in filter string: ${filter}`)
    }
}

function createDate(days) {
    const orig_date = new Date()
    const date = new Date(
        orig_date.getFullYear(),
        orig_date.getMonth(),
        orig_date.getDate(),
        0,
        0,
        0
    )
    date.setDate(date.getDate() + days)
    return date
}

function filterToRegex(searchString) {
    // Users are not expected to know regex even though that what we're using under the hood.
    // Instead, allow using * as wildcard and treat . as a string
    if (searchString === null) {
        return new RegExp('.*')
    } else {
        return new RegExp(`${searchString.replace('.', '\\.').replace('*', '.+')}`, 'i')
    }
}
