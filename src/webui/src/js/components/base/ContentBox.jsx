import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'

import { AClip } from './AClip.jsx'

const ContentBoxContainer = styled.div`
    background-color: rgba(49, 96, 129, 0.05);
    margin: 0.35rem;
    display: flex;
    height: calc(100% - 0.7rem);
`

const ContentBoxTitlebar = styled.div`
    height: auto;
    display: flex;
    min-height: 3.8rem;
    background-color: ${(p) => (p.disabled ? 'rgba(0, 0, 0, 0.25)' : 'rgba(49, 96, 129, 0.5)')};
    & > div {
        margin: 1.75rem 0;
    }
`

const ContentBoxBody = styled.div`
    padding: 1.3rem;
    width: 100%;

    font-size: 1.4rem;
    color: #333;
    font-weight: 300;
    word-wrap: break-word;
    word-break: break-word;
    font-family: 'Work Sans', sans-serif;
`

const ContentBoxTitlebarTitle = styled.span`
    color: white;
    font-family: 'Source Sans Pro', sans-serif;
    transform: rotate(180deg);
    writing-mode: vertical-lr;
    width: 2.8rem;
    line-height: 2.8rem;
    font-weight: 700;
    letter-spacing: 0.1rem;
    font-size: 1.3rem;
    text-transform: uppercase;
    white-space: nowrap;
    a {
        border-bottom: none;
        border-left: 1px dashed rgba(255, 255, 255, 0.6);
        &:hover {
            border-bottom: none;
            border-left: 1px solid rgb(255, 255, 255, 0.7);
        }
    }
`

export const ContentBoxWarning = styled.div`
    color: white;
    background-color: rgba(129, 62, 49, 0.75);
    font-size: 1.5rem;
    padding: 0.3rem 1rem;
    margin-bottom: 1rem;
    font-family: 'Source Sans Pro', sans-serif;
    font-weight: 400;
`

export const ContentBox = ({ title, titleUrl, disabled, children }) => {
    const cbTitle = titleUrl ? <AClip href={titleUrl}>{title}</AClip> : title
    return (
        <ContentBoxContainer>
            <ContentBoxTitlebar disabled={disabled}>
                <div>
                    <ContentBoxTitlebarTitle>{cbTitle}</ContentBoxTitlebarTitle>
                </div>
            </ContentBoxTitlebar>
            {disabled ? null : <ContentBoxBody>{children}</ContentBoxBody>}
        </ContentBoxContainer>
    )
}

ContentBox.propTypes = {
    title: PropTypes.string,
    titleUrl: PropTypes.string,
    disabled: PropTypes.bool
}
