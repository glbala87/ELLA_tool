import React from 'react'
import PropTypes from 'prop-types'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { ContentBox } from '../base'
import { FrequencyDetails } from './FrequencyDetails.jsx'

export const AlleleInfoFrequencyGnomadGenomes = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoFrequencyGnomadGenomes({ allele, allelePath }) {
        const hasContent = allele && allele.annotation.frequencies.GNOMAD_GENOMES

        return (
            <ContentBox title="gnomAD Genomes" titleUrl={allele.urls.gnomad} disabled={!hasContent}>
                <FrequencyDetails allelePath={allelePath} group="GNOMAD_GENOMES" />
            </ContentBox>
        )
    }
)

AlleleInfoFrequencyGnomadGenomes.propTypes = {
    allelePath: PropTypes.string.isRequired
}
