import React from 'react'
import PropTypes from 'prop-types'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/react'
import { state, signal, props } from 'cerebral/tags'

const COLUMNS = [
    {
        header: {
            title: 'Sample type',
            text: 'S'
        }
    },
    {
        header: {
            title: 'Inheritance',
            text: 'INH'
        }
    },
    {
        header: {
            title: 'Gene',
            text: 'GENE'
        }
    },
    {
        header: {
            title: 'HGVSc',
            text: 'HGVSc'
        }
    },
    {
        header: {
            title: 'CSQ',
            text: 'CSQ'
        }
    },
    {
        header: {
            title: 'Warnings',
            text: '!',
            indicator: true
        }
    }
]

const HeaderCell = ({ title, indicator, clickHandler, sorted, children }) => {
    let sortArrow = ''
    if (sorted === 'asc') {
        sortArrow = '↓'
    } else if (sorted === 'desc') {
        sortArrow = '↑'
    }
    const classNames = ['cell']
    if (indicator) {
        classNames.push('top')
    }
    return (
        <div className={classNames} title={title} onClick={clickHandler}>
            {children}
            <span>
                <span>{sortArrow}</span>
            </span>
        </div>
    )
}

const Header = ({}) => {
    const headerCells = COLUMNS.map((c) => (
        <HeaderCell title={c.header.title} key={c.header.text} indicator={c.header.indicator}>
            {c.header.text}
        </HeaderCell>
    ))
    return <div className="nav-row top">{headerCells}</div>
}

const getAlleles = (alleleIds, alleles) => {
    return Compute(alleleIds, alleles, (alleleIds, alleles) => {
        if (!alleleIds || !alleles) {
            return
        }
        return alleleIds.map((aId) => alleles[aId]).filter((a) => a !== undefined)
    })
}

const AlleleSidebarList = connect(
    {
        alleles: getAlleles(state`${props`alleleIdsPath`}`, state`${props`allelesPath`}`)
    },
    function AlleleSidebarList(props) {
        const numVariants = props.alleles.length
        return (
            <div className="allele-sidebar-list">
                <h4 className="section-title">
                    {props.sectionTitle} ({numVariants})
                </h4>
                <section className="allele-sidebar-list">
                    <div className="nav-table" ng-class="{'expanded': $ctrl.expanded}">
                        <Header />
                    </div>
                </section>
            </div>
        )
    }
)

AlleleSidebarList.propTypes = {
    sectionTitle: PropTypes.string.isRequired,
    alleleIdsPath: PropTypes.string.isRequired,
    allelesPath: PropTypes.string.isRequired
}

export default AlleleSidebarList
