import thenBy from 'thenby'

export default function updateMessages({ state }) {
    const logs = state.get('views.workflows.data.interpretationlogs')
    const interpretations = state.get('views.workflows.data.interpretations')
    const messages = []

    if (logs || interpretations) {
        // Ids can overlap between objects, so rename the id for tracking
        // to work correctly
        for (const l of Object.values(logs)) {
            let new_l = Object.assign({}, l)
            new_l.originalId = l.id
            new_l.id = 'log_' + l.id
            new_l.type = 'interpretationlog'
            messages.push(new_l)
        }
        for (const i of interpretations) {
            if (i.status === 'Done') {
                let new_i = {
                    id: i.id,
                    type: 'interpretation',
                    user: i.user,
                    workflow_status: i.workflow_status,
                    status: i.status,
                    date_last_update: i.date_last_update,
                    finalized: i.finalized
                }
                new_i.originalId = i.id
                new_i.id = 'interpretation_' + i.id
                messages.push(new_i)
            }
        }
        messages.sort(thenBy((m) => m.date_last_update || m.date_created))
    }
    // Get count of user messages since last finalized
    let messageCount = 0
    for (const m of messages) {
        if (m.message) {
            messageCount += 1
        }
        if (m.finalized) {
            messageCount = 0
        }
    }

    state.set('views.workflows.worklog.messageCount', messageCount)
    state.set('views.workflows.worklog.messageIds', messages.map((m) => m.id))
    const mappedMessages = {}
    for (const m of messages) {
        mappedMessages[m.id] = m
    }
    state.set('views.workflows.worklog.messages', mappedMessages)
}
