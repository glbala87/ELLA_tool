/* jshint esnext: true */

import { Reference } from '../../model/reference'
import { Service, Inject } from '../../ng-decorators'

@Service({
    serviceName: 'ReferenceResource'
})
@Inject('$resource')
class ReferenceResource {
    constructor(resource) {
        this.resource = resource
        this.base = '/api/v1'
    }

    createFromRaw(raw) {
        let data = {
            raw
        }
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/references/`, {}, { create: { method: 'POST' } })
            r.create(
                data,
                (o) => {
                    resolve(o)
                },
                reject
            )
        })
    }

    createFromManual(manualReference) {
        let journal = manualReference.journal
        if (
            manualReference.volume.length ||
            manualReference.issue.length ||
            manualReference.pages.length
        ) {
            journal += ': '
        }

        if (manualReference.volume.length) {
            journal += manualReference.volume
        }
        if (manualReference.issue.length) {
            journal += '(' + manualReference.issue + ')'
        }
        if (manualReference.pages.length) {
            if (manualReference.volume.length || manualReference.issue.length) {
                journal += ', '
            }
            journal += manualReference.pages
        }
        journal += '.'
        let data = {
            manual: {
                authors: manualReference.authors,
                title: manualReference.title,
                journal: journal,
                abstract: manualReference.abstract,
                year: manualReference.year,
                published: manualReference.published
            }
        }
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/references/`, {}, { create: { method: 'POST' } })
            r.create(
                data,
                (o) => {
                    resolve(o)
                },
                reject
            )
        })
    }

    getByPubMedIds(pmids) {
        return new Promise((resolve, reject) => {
            if (!pmids.length) {
                resolve([])
            }
            let q = JSON.stringify({ pubmed_id: pmids })
            let r = this.resource(`${this.base}/references/?q=${encodeURIComponent(q)}`)
            let references = r.query(() => {
                let refs = []
                for (let o of references) {
                    refs.push(new Reference(o))
                }
                resolve(refs)
            })
        })
    }

    getByIds(ids) {
        return new Promise((resolve, reject) => {
            if (!ids.length) {
                resolve([])
            }
            let q = JSON.stringify({ id: ids })
            let r = this.resource(`${this.base}/references/?q=${encodeURIComponent(q)}`)
            let references = r.query(() => {
                let refs = []
                for (let o of references) {
                    refs.push(new Reference(o))
                }
                resolve(refs)
            })
        })
    }

    getReferenceAssessments(allele_ids, reference_ids) {
        let q = JSON.stringify({
            date_superceeded: null,
            allele_id: allele_ids,
            reference_id: reference_ids,
            status: 1
        })
        return new Promise((resolve) => {
            let r = this.resource(`${this.base}/referenceassessments/?q=${encodeURIComponent(q)}`)
            let result = r.query(() => {
                resolve(result)
            })
        })
    }

    createOrUpdateReferenceAssessment(ra) {
        return new Promise((resolve) => {
            let r = this.resource(
                `${this.base}/referenceassessments/`,
                {},
                { createOrUpdate: { method: 'POST' } }
            )
            r.createOrUpdate(ra, (o) => {
                resolve(o)
            })
        })
    }

    search(searchString, per_page) {
        return new Promise((resolve) => {
            if (searchString.length < 3) {
                resolve([])
            } else {
                let s = JSON.stringify({ search_string: searchString })
                let r = this.resource(
                    `${this.base}/references/?s=${encodeURIComponent(s)}&per_page=${per_page}`
                )
                let references = r.query(() => {
                    let refs = []
                    for (let o of references) {
                        refs.push(new Reference(o))
                    }
                    resolve(refs)
                })
            }
        })
    }
}

export default ReferenceResource
