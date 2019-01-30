import React from 'react'
import PropTypes from 'prop-types'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { AClip, ContentBox } from '../base'

export const AlleleInfoDbsnp = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoDbsnp({ allele }) {
        const hasContent =
            allele && allele.annotation.filtered.some((t) => 'dbsnp' in t && t.dbsnp.length)
        const hasMultiple = allele.annotation.filtered.length > 1

        const items = allele.annotation.filtered.map((t) => {
            return (
                <p key={t.transcript}>
                    <AClip
                        href={`http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${t.dbsnp}`}
                    >
                        {t.dbsnp} {hasMultiple ? ` (${t.transcript})` : ''}
                    </AClip>
                </p>
            )
        })

        return (
            <ContentBox title="dbSNP" disabled={!hasContent}>
                {items}{' '}
            </ContentBox>
        )
    }
)

AlleleInfoDbsnp.propTypes = {
    allelePath: PropTypes.string.isRequired
}
