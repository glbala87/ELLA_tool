import React from 'react'
import PropTypes from 'prop-types'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { ContentBox } from '../base'
import { FrequencyDetails } from './FrequencyDetails.jsx'

export const AlleleInfoFrequencyGnomadExomes = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoFrequencyGnomadExomes({ allele, allelePath }) {
        const hasContent = allele && allele.annotation.frequencies.GNOMAD_EXOMES

        return (
            <ContentBox title="gnomAD Exomes" titleUrl={allele.urls.gnomad} disabled={!hasContent}>
                <FrequencyDetails allelePath={allelePath} group="GNOMAD_EXOMES" />
            </ContentBox>
        )
    }
)

AlleleInfoFrequencyGnomadExomes.propTypes = {
    allelePath: PropTypes.string.isRequired
}
