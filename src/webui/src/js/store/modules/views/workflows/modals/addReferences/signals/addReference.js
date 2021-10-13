import { set, push, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'
import createReference from '../actions/createReference'

const parseManual = ({ props }) => {
    const { title, authors, journal, volume, issue, year, pages, abstract, submode } = props
    let manual = {
        title,
        authors,
        journal,
        volume,
        issue,
        year,
        pages,
        abstract,
        published: submode != 'Unpublished'
    }

    // Remove empty values
    Object.keys(manual).forEach((key) => {
        if (manual[key] === '') {
            delete manual[key]
        }
    })

    if ('volume' in manual) {
        manual['journal'] += `: ${manual['volume']}`
        delete manual['volume']
    }

    if ('issue' in manual) {
        manual['journal'] += `(${manual['issue']})`
        delete manual['issue']
    }

    if ('pages' in manual) {
        manual['journal'] += `, ${manual['pages']}`
        delete manual['pages']
    }

    manual['journal'] += '.'

    return { data: { manual } }
}

export default [
    equals(state`views.workflows.modals.addReferences.referenceMode`),
    {
        Search: [
            set(
                state`views.workflows.modals.addReferences.data.references.${props`refId`}`,
                props`reference`
            ),
            push(state`views.workflows.modals.addReferences.userReferenceIds`, props`refId`)
        ],
        PubMed: [
            ({ props }) => {
                const { pubmedData } = props
                return { data: { pubmedData: pubmedData } }
            },
            createReference,
            {
                success: [
                    set(
                        state`views.workflows.modals.addReferences.data.references.${props`refId`}`,
                        props`reference`
                    ),
                    push(state`views.workflows.modals.addReferences.userReferenceIds`, props`refId`)
                ],
                error: [
                    toast(
                        'error',
                        'Failed to create reference. Please check that the data is correct.'
                    )
                ]
            }
        ],
        Manual: [
            parseManual,
            createReference,
            {
                success: [
                    set(
                        state`views.workflows.modals.addReferences.data.references.${props`refId`}`,
                        props`reference`
                    ),
                    push(state`views.workflows.modals.addReferences.userReferenceIds`, props`refId`)
                ],
                error: [
                    toast(
                        'error',
                        'Failed to create reference. Please check that the data is correct.'
                    )
                ]
            }
        ]
    }
]
