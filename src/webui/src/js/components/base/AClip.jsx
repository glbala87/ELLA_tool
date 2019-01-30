import copy from 'copy-to-clipboard'
import toastr from 'toastr'
import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { connect } from '@cerebral/react'
import { state } from 'cerebral/tags'

const CopySpan = styled.a`
    text-decoration: none;
    border-bottom: 1px dashed;
    border-color: rgba(0, 0, 0, 0.25);
    cursor: pointer;

    &:hover {
        text-decoration: none;
        border-bottom: 1px solid;
    }
`

export const AClip = connect(
    {
        config: state`app.config`
    },
    function AClip({ href, children, config }) {
        const shouldCopy = config.app.links_to_clipboard || false

        const clickHandler = (e) => {
            e.preventDefault()
            copy(href)
            toastr.info('Copied link to clipboard.', null, 1000)
            console.log(`Copied ${href} to clipboard.`)
        }

        return shouldCopy ? (
            <CopySpan href={href} onClick={clickHandler}>
                {children}
            </CopySpan>
        ) : (
            <a href={href} target="_new">
                {children}
            </a>
        )
    }
)

AClip.propTypes = {
    href: PropTypes.string.isRequired,
    children: PropTypes.node.isRequired
}
