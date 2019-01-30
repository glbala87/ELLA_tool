import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import { AClip, ContentBox } from '../base'
import { ContentBoxTable, ContentBoxTableRow, ContentBoxTableCell } from '../base'
import getClinvarAnnotation from '../../store/common/computes/getClinvarAnnotation'

const Star = ({ filled }) => {
    const styles = {
        width: '1rem',
        height: '1rem',
        strokeWidth: '3%',
        stroke: 'rgba(0, 0, 0, 0.75)',
        marginRight: '0.2rem'
    }
    if (filled) {
        styles.fill = 'rgba(0, 0, 0, 0.75)'
    }

    return (
        <svg
            id="i-star"
            style={styles}
            viewBox="0 0 32 32"
            width="32"
            height="32"
            fill="none"
            stroke="currentcolor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="6.25%"
        >
            <path d="M16 2 L20 12 30 12 22 19 25 30 16 23 7 30 10 19 2 12 12 12 Z" />
        </svg>
    )
}

const ReviewStatus = styled.span`
    margin-right: 0.8rem;
`

const Submission = styled.p`
    margin: 0.2rem 0;
`

export const AlleleInfoClinvar = connect(
    {
        allele: state`${props`allelePath`}`,
        clinvarAnnotation: getClinvarAnnotation(state`${props`allelePath`}`)
    },
    function AlleleInfoClinvar({ allele, clinvarAnnotation }) {
        const hasContent = clinvarAnnotation.items && clinvarAnnotation.items.length

        let starElem = null
        let submissions = null
        if (hasContent) {
            const stars = []
            for (let i = 1; i <= clinvarAnnotation.maxStarCount; i++) {
                const filled = i <= clinvarAnnotation.starCount
                stars.push(<Star filled={filled} key={i.toString()} />)
            }
            starElem = <span>{stars}</span>
            console.log(stars)

            submissions = clinvarAnnotation.items.map((item) => {
                return (
                    <Submission key={item.lastEvaluated + item.submitter}>
                        {item.lastEvaluated} - {item.sigText} - {item.phenotypeText} -{' '}
                        {item.submitter}
                    </Submission>
                )
            })
        }

        return (
            <ContentBox title="Clinvar" titleUrl={allele.urls.clinvar} disabled={!hasContent}>
                <ContentBoxTable>
                    <ContentBoxTableRow>
                        <ContentBoxTableCell>
                            <ReviewStatus>Review status:</ReviewStatus> {starElem} (
                            {clinvarAnnotation.revText})
                        </ContentBoxTableCell>
                    </ContentBoxTableRow>
                    <ContentBoxTableRow>
                        <ContentBoxTableCell>Submissions:</ContentBoxTableCell>
                    </ContentBoxTableRow>
                    <ContentBoxTableRow>
                        <ContentBoxTableCell>{submissions}</ContentBoxTableCell>
                    </ContentBoxTableRow>
                </ContentBoxTable>
            </ContentBox>
        )
    }
)

AlleleInfoClinvar.propTypes = {
    allelePath: PropTypes.string.isRequired
}
