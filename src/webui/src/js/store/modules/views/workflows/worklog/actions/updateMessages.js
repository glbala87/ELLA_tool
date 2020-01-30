import thenBy from 'thenby'

export default function updateMessages({ state }) {
    const logData = state.get('views.workflows.data.interpretationlogs')
    const interpretations = state.get('views.workflows.data.interpretations')
    const showMessagesOnly = state.get('views.workflows.worklog.showMessagesOnly')
    const messages = []

    if (logData && logData.logs) {
        // We mix log items from backend and creating own interpretations events.
        // Therefore, we need to prepend the ids as they could both have same id
        for (const l of logData.logs) {
            let new_l = Object.assign({}, l)
            new_l.originalId = l.id
            new_l.id = 'log_' + l.id
            new_l.type = 'interpretationlog'
            new_l.user = logData.users.find((u) => u.id === l.user_id)
            messages.push(new_l)
        }
    }

    if (interpretations) {
        for (const i of interpretations) {
            if (i.status === 'Done' && i.finalized) {
                let new_i = {
                    id: 'interpretation_' + i.id,
                    originalId: i.id,
                    type: 'interpretation',
                    user: i.user,
                    workflow_status: i.workflow_status,
                    status: i.status,
                    date_last_update: i.date_last_update,
                    finalized: i.finalized
                }
                messages.push(new_i)
            }
        }
    }

    messages.sort(thenBy((m) => m.date_last_update || m.date_created))

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
    state.set(
        'views.workflows.worklog.messageIds',
        messages.filter((m) => (showMessagesOnly ? Boolean(m.message) : true)).map((m) => m.id)
    )
    const mappedMessages = {}
    for (const m of messages) {
        mappedMessages[m.id] = m
    }
    state.set('views.workflows.worklog.messages', mappedMessages)
}
