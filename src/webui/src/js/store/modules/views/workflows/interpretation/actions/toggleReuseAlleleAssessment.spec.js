import {runAction} from 'cerebral/test'
import toggleReuseAlleleAssessment from './toggleReuseAlleleAssessment'


describe('toggleReuseAlleleAssessment',  () => {

        const createState = (resuseFlag=false) => {
        return {
            views: {
                workflows: {
                    data: {
                        alleles: {
                            1: {
                                id: 1,
                                allele_assessment: {
                                    dummy: "Just to have something here",
                                    id: 45
                                }
                            }
                        }
                    },
                interpretation: {
                    selected: {
                        state: {
                            allele: {
                                1: {
                                    alleleassessment: { reuse: resuseFlag}
                                }
                            }
                        }
                    }
                }

                }
            }
        }

    }

    it("changes to 'no reuse' when initially reused", () => {
        runAction(toggleReuseAlleleAssessment, {state: createState(true), props: {alleleId: 1}}).then(
            ({ state, output }) => {
                expect(state.views.workflows.interpretation.selected.state.allele[1].alleleassessment.reuse)
                    .toBe(false)
                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([1])
            }).catch((reason) => console.error(reason.payload.error))
    })

    it("changes to 'reuse' when initially not reused", () => {
        runAction(toggleReuseAlleleAssessment, {state: createState(false), props: {alleleId: 1}}).then(
            ({ state }) => {
                expect(state.views.workflows.interpretation.selected.state.allele[1].alleleassessment.reuse)
                    .toBe(true)
                expect(state.views.workflows.interpretation.selected.state.allele[1].alleleassessment)
                    .toEqual({
                        allele_id: 1,
                        reuse: true,
                        reuseCheckedId: 45
                    })

                expect(output.copyExistingAlleleAssessmentAlleleIds).toEqual([])

            }).catch((reason) => console.error(reason.payload.error))
    })
})