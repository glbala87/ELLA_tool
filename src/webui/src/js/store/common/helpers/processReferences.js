export default function processReferences(references) {
    for (let reference of references) {
        reference.urls = getUrls(reference)
        reference.formatted = getFormatted(reference)
    }
}

function getUrls(reference) {
    const urls = {}
    if (reference.pubmed_id) {
        urls.pubmed = `http://www.ncbi.nlm.nih.gov/pubmed/${reference.pubmed_id}`
    }
    return urls
}

function getFormatted(reference) {
    const formatted = {}

    //
    // name
    //
    formatted.shortDesc = ''
    let shortDesc = reference.authors
    if (reference.year !== undefined && reference.year.length > 0) {
        shortDesc += ` (${reference.year})`
    }
    shortDesc += `, ${reference.journal}`
    formatted.shortDesc = shortDesc

    return formatted
}
