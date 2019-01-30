import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { ContentBox } from '../base'

export const AlleleInfoHgmd = connect(
    {
        allele: state`${props`allelePath`}`
    },
    function AlleleInfoHgmd({ allele }) {
        const hasContent = Boolean(allele.annotation.external.HGMD)
        let content = null
        if (hasContent) {
            content = [
                <p key="tag">{allele.annotation.external.HGMD.tag}</p>,
                <p key="disease">{allele.annotation.external.HGMD.disease}</p>,
                <p key="acc_num">{allele.annotation.external.HGMD.acc_num}</p>
            ]
        }
        return (
            <ContentBox title="HGMD" titleUrl={allele.urls.hgmd} disabled={!hasContent}>
                {content}
            </ContentBox>
        )
    }
)

AlleleInfoHgmd.propTypes = {
    allelePath: PropTypes.string.isRequired
}
