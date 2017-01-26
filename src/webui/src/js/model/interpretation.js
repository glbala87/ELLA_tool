/* jshint esnext: true */


export const STATUS_ONGOING = "Ongoing";
export const STATUS_NOT_STARTED = "Not started";

export class Interpretation {


    /**
     * Represents one Interpretation.
     * @param  {object} Interpretation data from server, see InterpretationResource
     */
    constructor(data) {
        Object.assign(this, data);
        this.dirty = false; // Indicates whether any state has changed, so user should save

    }

    /**
     * Call this function whenever the Interpretation's state has been updated.
     */
    setDirty() {
        this.dirty = true;
    }

    setClean() {
        this.dirty = false;
    }

    isOngoing() {
        return this.status == STATUS_ONGOING;
    }

}
