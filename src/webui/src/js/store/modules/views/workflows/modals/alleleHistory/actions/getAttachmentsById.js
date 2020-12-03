export default function getAttachmentsById({ props, http, path }) {
    const { attachmentIds } = props

    const params = {
        q: JSON.stringify({ id: attachmentIds })
    }
    return http
        .get('attachments/', params)
        .then((response) => {
            const attachmentsById = {}
            for (let r of response.result) {
                attachmentsById[r.id] = r
            }
            return path.success({ result: attachmentsById })
        })
        .catch((error) => {
            console.error(error)
            return path.error({ result: response.result })
        })
}
