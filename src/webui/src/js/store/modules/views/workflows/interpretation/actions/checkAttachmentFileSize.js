export default function checkAttachmentFileSize({ state, path, props }) {
    const config = state.get('app.config')
    const { file } = props
    if (file.size <= config.app.max_upload_size) {
        return path.valid()
    }
    return path.invalid()
}
