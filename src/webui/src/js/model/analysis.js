/* jshint esnext: true */

class Analysis {
    /**
     * Represents one Analysis.
     * @param  {object} Analysis data from server.
     */
    constructor(data) {
        console.log(data);
        this.id = data.id;
        this.interpretations = data.interpretations;

        // DEBUG:
        for (let i of this.interpretations) {
            i.user = {
                firstName: "First",
                lastName: "User",
            };
        }
        this.interpretations[0].status = 'Done';
        this.interpretations.push(Object.assign({}, this.interpretations[0]));
        this.interpretations[1].user = {firstName: 'Second', lastName: 'User'};
        console.log(this.interpretations);
        this.interpretations[1].id = this.interpretations[0].id + 100;
        this.interpretations[1].status = 'Not started';
        //

        this.name = data.name;
        this.genepanel = data.genepanel;
    }

    getInterpretationState() {
        var STATE_PRIORITY = ['Not started', 'Ongoing', 'Done'];
        let states = this.interpretations.map(x => x.status);
        if (states.length) {
            return states.sort(x => STATE_PRIORITY.indexOf(x))[0];
        }
    }

    getInterpretationId() {
        // TODO: implement me
        return this.interpretations[0].id;
    }
}
