import React from 'react'
import PropTypes from 'prop-types'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { ContentBox } from '../base'
import { FrequencyDetails } from './FrequencyDetails.jsx'

export const AlleleInfoFrequencyIndb = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoFrequencyIndb({ allele, allelePath }) {
        const hasContent = allele && allele.annotation.frequencies.inDB

        return (
            <ContentBox title="inDB" disabled={!hasContent}>
                <FrequencyDetails allelePath={allelePath} group="inDB" />
            </ContentBox>
        )
    }
)

AlleleInfoFrequencyIndb.propTypes = {
    allelePath: PropTypes.string.isRequired
}
