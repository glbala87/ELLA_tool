import { Module } from 'cerebral'
import { CerebralTest } from 'cerebral/test'
import callerTypeSelectedChanged from '../signals/callerTypeSelectedChanged'

import mock from 'xhr-mock'
import RootModule from '../../../..'

function alleleFactory() {
    return {
        1: {
            id: 1,
            caller_type: 'snv',
            annotation: {}
        },
        2: {
            id: 2,
            caller_type: 'snv',
            annotation: {}
        },
        3: {
            id: 3,
            caller_type: 'cnv',
            chromosome: 2,
            annotation: {}
        },
        4: {
            id: 4,
            caller_type: 'cnv',
            chromosome: 1,
            annotation: {}
        },
        5: {
            id: 5,
            caller_type: 'cnv',
            chromosome: 'X',
            start_position: 10,
            annotation: {}
        },
        6: {
            id: 6,
            caller_type: 'snv',
            annotation: {}
        },
        7: {
            id: 7,
            caller_type: 'cnv',
            chromosome: 'X',
            start_position: 11,
            open_end_position: 14,
            annotation: {}
        },
        8: {
            id: 8,
            caller_type: 'cnv',
            chromosome: 'X',
            start_position: 11,
            open_end_position: 12,
            annotation: {}
        }
    }
}

function enrichAllele() {
    let obj = alleleFactory()
    for (let a in obj) {
        Object.assign(obj[a], {
            analysis: { verification: '' }
        })
    }
    return obj
}

function alleleSidebarFactory(
    callerTypeSelected = 'snv',
    unclassified = [],
    classified = [],
    technical = [],
    notRelevant = []
) {
    return {
        callerTypeSelected,
        unclassified,
        classified,
        technical,
        notRelevant,
        orderBy: {
            unclassified: {},
            classified: {},
            technical: {},
            notRelevant: {}
        }
    }
}

function testState(alleles, alleleSidebar) {
    return {
        selectedComponent: 'Classification',
        selectedAllele: null,
        alleleSidebar,
        interpretation: {
            state: {
                allele: enrichAllele()
            },
            userState: {},
            data: {
                alleles: alleles
            }
        }
    }
}

let cerebral = null

describe('prepareSelectedAllele', function() {
    beforeEach(() => {
        mock.setup()
        cerebral = CerebralTest(RootModule(false), {})
        cerebral.controller.addModule(
            'test',
            new Module({
                state: {},
                signals: {
                    callerTypeSelectedChanged
                }
            })
        )
    })
    afterEach(() => mock.teardown())

    it('should handle empty allele array', async () => {
        const testContext = testState({}, alleleSidebarFactory())
        cerebral.setState('views.workflows', testContext)
        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelcted: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(null)
    })

    it('should select the first unclassified allele for cnv when switching to callerTypeSelected = cnv', async () => {
        const testData = alleleFactory()
        const sidebar = alleleSidebarFactory('snv', [1, 2, 4, 3], [], [5], [6])
        const testContext = testState(testData, sidebar)
        cerebral.setState('views.workflows', testContext)

        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelected: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(4)
    })

    it('should correctly sort cnvs based on start_position when on same chromosome', async () => {
        let testData = alleleFactory()
        delete testData[3]
        delete testData[4]

        const sidebar = alleleSidebarFactory('snv', [1, 2, 5, 7], [], [5], [6])
        const testContext = testState(testData, sidebar)
        cerebral.setState('views.workflows', testContext)

        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelected: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(5)
    })

    it('should correctly sort cnvs based on open_end_position when on same chromosome and same start_position', async () => {
        let testData = alleleFactory()
        delete testData[3]
        delete testData[4]
        delete testData[5]

        const sidebar = alleleSidebarFactory('snv', [1, 2, 7, 8], [], [5], [6])
        const testContext = testState(testData, sidebar)
        cerebral.setState('views.workflows', testContext)

        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelected: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(8)
    })
})
