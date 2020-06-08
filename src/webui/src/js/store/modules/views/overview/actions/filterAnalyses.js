export default function filterAnalyses({ state }) {
    const analyses = state.get('views.overview.data.analyses')
    const filter = state.get('views.overview.filter')

    if (!filter || !Object.values(filter).some((x) => x !== null && x !== '')) {
        state.set('views.overview.filteredAnalyses', analyses)
    } else {
        const filteredAnalyses = {}
        const nameMatch = new RegExp(`.*${filter.analysisName}.*`, 'i')
        // allow using * as an alias for regex .
        const commentMatch = new RegExp(
            `.*${filter.reviewComment == '*' ? '.' : filter.reviewComment}.*`,
            'i'
        )

        for (let [sectionName, sectionAnalyses] of Object.entries(analyses)) {
            filteredAnalyses[sectionName] = sectionAnalyses.filter((a) => {
                return (
                    (!filter.analysisName || nameMatch.test(a.name)) &&
                    (!filter.reviewComment ||
                        (a.review_comment && commentMatch.test(a.review_comment))) &&
                    ((!filter.technologySanger && !filter.technologyHTS) ||
                        (filter.technologySanger && a.technology == 'Sanger') ||
                        (filter.technologyHTS && a.technology == 'HTS')) &&
                    ((!filter.priorityNormal && !filter.priorityHigh && !filter.priorityUrgent) ||
                        (filter.priorityNormal && a.priority == 1) ||
                        (filter.priorityHigh && a.priorty == 2) ||
                        (filter.priorityUrgent && a.priority == 3)) &&
                    (!filter.dateRange || withinRange(filter.dateRange, new Date(a.date_requested)))
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
    if (unit == 'd') {
        filterDate = createDate(Number(amount), 0)
    } else if (unit == 'm') {
        filterDate = createDate(0, Number(amount))
    } else {
        throw new SyntaxError(`Invalid unit in filter string: ${filter}`)
    }

    // only using lt, ge now, but might as well support others
    if (op == 'lt') {
        return filterDate < date
    } else if (op == 'le') {
        return filterDate <= date
    } else if (op == 'gt') {
        return filterDate > date
    } else if (op == 'ge') {
        return filterDate >= date
    } else {
        throw new SyntaxError(`Invalid operation in filter string: ${filter}`)
    }
}

function createDate(days, months) {
    const orig_date = new Date()
    const date = new Date(orig_date.getTime())
    date.setHours(0)
    date.setMinutes(0)
    date.setSeconds(0)
    date.setMilliseconds(0)
    date.setDate(date.getDate() + days)
    date.setMonth(date.getMonth() + months)

    // time is hard and js month math is bad, e.g.
    // date = new Date(2020, 2, 30) -> Mon Mar 30 2020 00:00:00
    // date.setMonth(date.getMonth() - 1) -> Sun Mar 01 2020 00:00:00
    // So we check what the real month delta is and adjust days as necessary
    while ((orig_date.getMonth() - date.getMonth() + 12) % 12 != Math.abs(months)) {
        date.setDate(date.getDate() - 1)
    }
    return date
}
