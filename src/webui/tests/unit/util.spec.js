import {hasDataAtKey} from "../../src/js/util";

describe("util", function () {
    it("gives true when keys are present", function () {
        expect(hasDataAtKey({"foo": "bar"}, "foo")).toBe(true)
        expect(hasDataAtKey({"foo": {"bar": 4}}, "foo", "bar")).toBe(true)
        expect(hasDataAtKey({"foo": {"bar": {"baz": 4}}}, "foo", "bar", "baz")).toBe(true)
    })

    it("gives false when keys are not present", function () {
        expect(hasDataAtKey({})).toBe(false)
        expect(hasDataAtKey({}, "name")).toBe(false)
        expect(hasDataAtKey({"age": 5}, "name")).toBe(false)
    })
})