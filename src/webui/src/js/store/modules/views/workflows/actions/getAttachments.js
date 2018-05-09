function getAttachments({ http, path, state }) {
    let alleles = state.get('views.workflows.data.alleles')
    let interpretation = state.get('views.workflows.interpretation.selected')

    // Get all attachment ids from alleles
    let attachmentIds = []
    for (let alleleId in interpretation.state.allele) {
        if (
            'alleleassessment' in interpretation.state.allele[alleleId] &&
            !interpretation.state.allele[alleleId].alleleassessment.reuse
        ) {
            attachmentIds = attachmentIds.concat(
                interpretation.state.allele[alleleId].alleleassessment.attachment_ids
            )
        }
    }
    for (let allele of Object.values(alleles)) {
        if ('allele_assessment' in allele) {
            attachmentIds = attachmentIds.concat(allele.allele_assessment.attachment_ids)
        }
    }
    attachmentIds = [...new Set(attachmentIds)]

    return http
        .get(`attachments/?q=${encodeURIComponent(JSON.stringify({ id: attachmentIds }))}`)
        .then((response) => {
            const attachments = {}
            for (let a of response.result) {
                attachments[a.id] = a
            }
            response.result = attachments
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getAttachments
