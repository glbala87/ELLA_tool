import React from 'react'
import PropTypes from 'prop-types'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { ContentBox } from '../base'
import { FrequencyDetails } from './FrequencyDetails.jsx'

export const AlleleInfoFrequencyExac = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoFrequencyExac({ allele, allelePath }) {
        const hasContent = allele && allele.annotation.frequencies.ExAC
        return (
            <ContentBox title="ExAC" titleUrl={allele.urls.exac} disabled={!hasContent}>
                <FrequencyDetails allelePath={allelePath} group="ExAC" />
            </ContentBox>
        )
    }
)

AlleleInfoFrequencyExac.propTypes = {
    allelePath: PropTypes.string.isRequired
}
