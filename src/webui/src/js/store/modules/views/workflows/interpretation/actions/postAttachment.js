export default function postAttachment({ http, path, props }) {
    return http
        .uploadFile('attachments/upload/', props.file, {
            name: 'file'
        })
        .then(response => {
            return path.success({ result: response.result })
        })
        .catch(response => {
            return path.error(response)
        })
}
