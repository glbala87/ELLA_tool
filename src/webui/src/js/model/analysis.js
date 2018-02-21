/* jshint esnext: true */
import Genepanel from './genepanel'

export default class Analysis {
    /**
     * Represents one Analysis.
     *
     * @param  {object} Analysis data from server, see api/v1/interpretations/
     */
    constructor(data) {
        Object.assign(this, data)
        this.genepanel = new Genepanel(data.genepanel)
    }

    getInterpretationState() {
        var STATE_PRIORITY = ['Not started', 'Ongoing', 'Done']
        let states = this.interpretations.map(x => x.status)
        if (states.length) {
            return states.sort(x => STATE_PRIORITY.indexOf(x))[0]
        }
    }

    getInterpretationId() {
        // TODO: implement me
        return this.interpretations[this.interpretations.length - 1].id
    }

    /**
     * Returns the user of the last interpretation for analysis.
     */
    getInterpretationUser() {
        return this.interpretations[this.interpretations.length - 1].user
    }
}
