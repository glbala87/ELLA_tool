import hypothesis as ht
import hypothesis.strategies as st
import re
from api.config.acmgconfig import acmgconfig
from rule_engine.grc import ACMGClassifier2015


classifier_rules = {
    5: [
        ["PVS", "PVS"],
        ["PVS", "PS"],
        ["PVS", "PM"],
        ["PVS", "PP", "PP"],
        ["PS", "PS"],
        ["PS", "PM", "PM", "PM"],
        ["PS", "PM", "PM", "PP", "PP"],
        ["PS", "PM", "PP", "PP", "PP", "PP"],
    ],
    4: [
        ["PVS", "PP"],
        ["PS", "PM"],
        ["PS", "PP", "PP"],
        ["PM", "PM", "PM"],
        ["PM", "PM", "PP", "PP"],
        ["PM", "PP", "PP", "PP", "PP"],
    ],
    2: [["BS", "BP"], ["BP", "BP"]],
    1: [["BA"], ["BS", "BS"]],
}

P = re.compile("P.*")
PVS = re.compile("PVS.*")
PS = re.compile("PS.*")
PM = re.compile("PM.*")
PP = re.compile("PP.*")
B = re.compile("B.*")
BA = re.compile("BA.*")
BS = re.compile("BS.*")
BP = re.compile("BP.*")

BASE_CODES = [c for c in acmgconfig["explanation"] if B.match(c) or P.match(c)]
# Strength, sorted by precedence
STRENGTHS = {"B": ["BA", "BS", "BP"], "P": ["PVS", "PS", "PM", "PP"]}


@st.composite
def code(draw):
    base_code = draw(st.sampled_from(BASE_CODES))
    if P.match(base_code):
        draw_from = STRENGTHS["P"]
    elif B.match(base_code):
        draw_from = STRENGTHS["B"]
    else:
        raise RuntimeError()
    strength = draw(st.sampled_from(draw_from))
    if strength in base_code:
        return base_code
    else:
        return "{}x{}".format(strength, base_code)


def list_subset(a, b):
    # Checks if a is subset of b
    c = list(a)
    for i, k in enumerate(b):
        if k in c:
            c.pop(c.index(k))
    return len(c) == 0


def get_strength(code):
    return re.sub(r"\d", "", code.split("x")[0])


def get_base_code(code):
    return code.split("x")[-1]


def extract_relevant(acmg_codes):
    """
    Remove duplicated base codes, keep only the strongest
    e.g. [PVSxPS1, PS1, PMxPS1, PMxPS2] -> [PVSxPS1, PMxPS2]
    """
    combined_strengths = STRENGTHS["P"] + STRENGTHS["B"]
    base_codes_added = set()
    relevant_acmg_codes = []
    for code in sorted(acmg_codes, key=lambda c: combined_strengths.index(get_strength(c))):
        base_code = get_base_code(code)
        if base_code not in base_codes_added:
            relevant_acmg_codes.append(code)
            base_codes_added.add(base_code)

    return relevant_acmg_codes


@ht.given(st.lists(code(), unique=True))
def test_suggested_classification(acmg_codes):
    relevant_acmg_codes = extract_relevant(acmg_codes)
    classifier = ACMGClassifier2015()
    classifier_class = classifier.classify(acmg_codes).clazz

    # Check that classifier extracts relevant acmg codes correct
    assert classifier_class == classifier.classify(relevant_acmg_codes).clazz

    strengths = [get_strength(c) for c in relevant_acmg_codes]
    if any(P.match(c) for c in acmg_codes) and any(B.match(c) for c in acmg_codes):
        # Contradicting
        possible_classes = []
    elif all(P.match(c) for c in relevant_acmg_codes):
        # Order important. Check the stricter criteria first
        possible_classes = [5, 4]
    elif all(B.match(c) for c in relevant_acmg_codes):
        # Order important. Check the stricter criteria first
        possible_classes = [1, 2]
    else:
        raise RuntimeError()

    # Order important.
    expected_class = 3
    for clazz in possible_classes:
        for rule in classifier_rules[clazz]:
            if list_subset(rule, strengths):
                expected_class = clazz
                break
        if expected_class != 3:
            break

    classifier = ACMGClassifier2015()
    classifier_class = classifier.classify(acmg_codes).clazz
    assert classifier_class == expected_class
