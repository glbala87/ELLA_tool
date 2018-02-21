const START_ACTIONS = {
    started: 'started analysing',
    started_review: 'started reviewing',
    review: 'reviewed'
}

const END_ACTIONS = {
    finalized: ' and finalized it',
    marked_review: ' and marked it for review'
}

export default function processOverviewActivities(activities, user) {
    for (let activity of activities) {
        activity.formatted = getFormatted(activity, user)
    }
}

function getFormatted(activity, user) {
    let formatted = {}
    //
    // start action
    //
    if (activity.start_action in START_ACTIONS) {
        formatted.startAction = START_ACTIONS[activity.start_action]
    } else {
        formatted.startAction = 'unknown'
    }

    //
    // end action
    //
    if (activity.end_action in END_ACTIONS) {
        formatted.endAction = END_ACTIONS[activity.end_action]
    } else {
        formatted.endAction = ''
    }

    //
    // activity name
    //
    if ('allele' in activity) {
        formatted.name = activity.allele.formatted.name
    }
    if ('analysis' in activity) {
        formatted.name = activity.analysis.name
    }

    //
    // user
    //
    if (activity.user.id == user.id) {
        formatted.user = 'You'
    } else {
        formatted.user = activity.user.full_name
    }

    return formatted
}
