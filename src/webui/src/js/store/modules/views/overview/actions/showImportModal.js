export default function showImportModal({ ImportModal, path }) {
    return ImportModal.show()
        .then(result => {
            return path.result()
        })
        .catch(result => {
            return path.dismissed()
        })
}
