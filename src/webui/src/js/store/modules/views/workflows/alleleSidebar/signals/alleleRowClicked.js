import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import selectedAlleleChanged from '../../sequences/selectedAlleleChanged'

export default [
    equals(state`views.workflows.selectedComponent`),
    {
        Classification: [
            set(state`views.workflows.selectedAllele`, props`alleleId`),
            ({ props }) => {
                console.log(`Selected allele id: ${props.alleleId}`)
            },
            selectedAlleleChanged
        ],
        otherwise: []
    }
]
