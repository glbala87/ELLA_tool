
import Annotation from "../../src/js/model/annotation.js"

describe("Annotation model", function () {


    // Mock data
    function getData() {
        return {
            "annotation_id": 37,
            "filtered_transcripts": [
                "NM_000123"
            ],
            "transcripts": [
                {
                    "symbol": "GENE1",
                    "Transcript": "NM_000123",
                    "Transcript_version": "1"
                },
                {
                    "symbol": "GENE2",
                    "Transcript": "NM_000321",
                    "Transcript_version": "3"
                }
            ],
            "worst_consequence": [
                "NM_000321"
            ]
        };

    }

    it("can be constructed", function () {
        expect(new Annotation(getData())).toBeDefined();
    });

    it("sets filtered transcripts ", function () {
        let annotation = new Annotation(getData());
        expect(annotation.filtered).toEqual(
            [{
                "symbol": "GENE1",
                "Transcript": "NM_000123",
                "Transcript_version": "1"
            }]
        );
    });

    it("reports correctly whether it has worse consequence", function () {
        let annotation = new Annotation(getData());
        expect(annotation.hasWorseConsequence()).toBeTruthy();

    });

    it("correctly returns worst consequence transcript", function () {
        let annotation = new Annotation(getData());
        expect(annotation.getWorseConsequenceTranscripts()).toEqual(
            [{
                "symbol": "GENE2",
                "Transcript": "NM_000321",
                "Transcript_version": "3"
            }]
        );

    });

});
