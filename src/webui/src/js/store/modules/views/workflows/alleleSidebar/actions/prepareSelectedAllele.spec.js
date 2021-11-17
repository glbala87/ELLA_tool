import { Module } from 'cerebral'
import { CerebralTest } from 'cerebral/test'
import callerTypeSelectedChanged from '../signals/callerTypeSelectedChanged'

import mock from 'xhr-mock'
import RootModule from '../../../..'

function alleleFactory() {
    return {
        1: {
            id: 1,
            caller_type: 'snv'
        },
        2: {
            id: 2,
            caller_type: 'snv'
        },
        3: {
            id: 3,
            caller_type: 'cnv'
        },

        4: {
            id: 4,
            caller_type: 'cnv'
        },
        5: {
            id: 5,
            caller_type: 'cnv'
        },
        6: {
            id: 6,
            caller_type: 'snv'
        }
    }
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
        notRelevant
    }
}

function testState(alleles, alleleSidebar) {
    return {
        selectedComponent: 'Classification',
        selectedAllele: null,
        alleleSidebar,
        interpretation: {
            state: {},
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
        const testContext = testState(null, alleleSidebarFactory())
        cerebral.setState('views.workflows', testContext)
        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelcted: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(null)
    })
    it('should select the first unclassified allele for cnv when switching to callerTypeSelected = cnv', async () => {
        const testData = alleleFactory()
        const sidebar = alleleSidebarFactory('snv', [1, 2, 3], [4], [5], [6])
        const testContext = testState(testData, sidebar)
        cerebral.setState('views.workflows', testContext)
        let result = await cerebral.runSignal('test.callerTypeSelectedChanged', {
            callerTypeSelected: 'cnv'
        })
        expect(result.state.views.workflows.selectedAllele).toBe(3)
    })
})
