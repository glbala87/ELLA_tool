from api.tests import interpretation_helper as ih


"""
Performs various interpretation rounds for analyses and alleles.
"""


def _assert_all_interpretations_are_done(interpretations):
    expected_status = "Done"
    assert all(
        [i["status"] == expected_status for i in interpretations]
    ), "Expected all to be {}".format(expected_status)


def _item_connected_to_allele_is_current(allele_id, items_source, expected_comment):
    items = [item for item in items_source if item["allele_id"] == allele_id]
    assert any(
        map(
            lambda a: a["date_superceeded"] is None
            and a["evaluation"]["comment"] == expected_comment,
            items,
        )
    ), "No assessment/report for allele {} that's current has comment '{}'".format(
        allele_id, expected_comment
    )


def _item_connected_to_allele_has_been_superceeded(allele_id, items_source, expected_comment):
    selected_items = [item for item in items_source if item["allele_id"] == allele_id]
    assert any(
        map(
            lambda a: a["date_superceeded"] is not None
            and a["evaluation"]["comment"] == expected_comment,
            selected_items,
        )
    ), "no assessment/report for allele {} that has been superceeded has the comment '{}' ".format(
        allele_id, expected_comment
    )


def _build_dummy_annotations(allele_ids):
    custom_annotations = list()  # currently left empty
    annotations = list()
    for id in allele_ids:
        annotations.append({"allele_id": id, "annotation_id": "1"})

    return annotations, custom_annotations


class WorkflowHelper(object):
    def __init__(
        self, workflow_type, workflow_id, genepanel_name, genepanel_version, filterconfig_id=None
    ):

        assert genepanel_name and genepanel_version

        if workflow_type == "analysis" and not filterconfig_id:
            raise RuntimeError("Missing required filterconfig id when workflow_type == 'analysis'")

        self.type = workflow_type
        self.id = workflow_id
        self.filterconfig_id = filterconfig_id
        self.genepanel_name = genepanel_name
        self.genepanel_version = genepanel_version
        self.interpretation_extras = {"gp_name": genepanel_name, "gp_version": genepanel_version}

    def _update_comments(self, state, comment):
        allele_assessments = state["alleleassessments"]
        reference_assessments = state["referenceassessments"]
        allele_reports = state["allelereports"]

        # Simulate updating the assessments in the state
        for s in allele_assessments + reference_assessments + allele_reports:
            s["evaluation"]["comment"] = comment

    def _check_comments(self, state, comment):
        allele_assessments = state["alleleassessments"]
        reference_assessments = state["referenceassessments"]
        allele_reports = state["allelereports"]

        assert all(
            [
                item["evaluation"]["comment"] == comment
                for item in allele_assessments + reference_assessments + allele_reports
            ]
        )

    def reopen(self, username):
        r = ih.reopen_analysis(self.type, self.id, username)
        assert r.status_code == 200
        return r.get_json()

    def start_interpretation(self, username):
        return ih.start_interpretation(
            self.type, self.id, username, extra=self.interpretation_extras
        )

    def perform_round(self, interpretation, comment, new_workflow_status="Interpretation"):
        """
        :param interpretation: interpretation object from start_interpretation()
        """

        # Utilize the interpretation state to store our data between test rounds
        # The format doesn't necessarily reflect how the frontend keep it's state.
        interpretation["state"].update(
            {"alleleassessments": list(), "referenceassessments": list(), "allelereports": list()}
        )
        if self.type == "analysis":
            allele_ids = ih.get_filtered_alleles(
                self.type, self.id, interpretation["id"], filterconfig_id=self.filterconfig_id
            ).get_json()["allele_ids"]
        else:
            allele_ids = [self.id]

        r = ih.get_alleles(self.type, self.id, interpretation["id"], allele_ids)
        assert r.status_code == 200
        alleles = r.get_json()

        # Put assessments and reports in the state:
        for allele in alleles:
            interpretation["state"]["alleleassessments"].append(
                ih.allele_assessment_template(
                    allele["id"], self.genepanel_name, self.genepanel_version
                )
            )

            annotation_references = allele["annotation"]["references"]
            ref_ids = [r["pubmed_id"] for r in annotation_references]
            q = {"pubmed_id": ref_ids}
            references = ih.get_entities_by_query("references", q).get_json()
            for reference in references:
                interpretation["state"]["referenceassessments"].append(
                    ih.reference_assessment_template(
                        allele["id"], reference["id"], self.genepanel_name, self.genepanel_version
                    )
                )

            interpretation["state"]["allelereports"].append(ih.allele_report_template(allele["id"]))

        self._update_comments(interpretation["state"], comment)

        ih.save_interpretation_state(
            self.type, interpretation, self.id, interpretation["user"]["username"]
        )

        interpretation_cnt = len(ih.get_interpretations(self.type, self.id).get_json())

        ih.save_interpretation_state(
            self.type, interpretation, self.id, interpretation["user"]["username"]
        )

        finish_method = {
            "Not ready": ih.mark_notready,
            "Interpretation": ih.mark_interpretation,
            "Review": ih.mark_review,
            "Medical review": ih.mark_medicalreview,
        }

        r = finish_method[new_workflow_status](
            self.type,
            self.id,
            ih.round_template(
                allele_ids=allele_ids
            ),  # We don't bother to provide real data for normal rounds, we are just testing workflow
            interpretation["user"]["username"],
        )
        assert r.status_code == 200

        # Check that new interpretation was created
        assert len(ih.get_interpretations(self.type, self.id).get_json()) == interpretation_cnt + 1

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type, self.id, interpretation["id"]
        ).get_json()

        self._check_comments(reloaded_interpretation["state"], comment)

        assert reloaded_interpretation["finalized"] is False
        assert reloaded_interpretation["status"] == "Done"
        assert reloaded_interpretation["user"]["username"] == interpretation["user"]["username"]

    def perform_finalize_round(self, interpretation, comment):

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation["state"]["alleleassessments"]
        reference_assessments = interpretation["state"]["referenceassessments"]
        allele_reports = interpretation["state"]["allelereports"]

        self._update_comments(interpretation["state"], comment)

        ih.save_interpretation_state(
            self.type, interpretation, self.id, interpretation["user"]["username"]
        )

        # check that no new interpretation is created
        interpretation_cnt = len(ih.get_interpretations(self.type, self.id).get_json())

        # annotations are needed when finalizing since it tracks their ids
        annotations, custom_annotations = _build_dummy_annotations(
            [a["allele_id"] for a in allele_assessments]
        )

        ih.save_interpretation_state(
            self.type, interpretation, self.id, interpretation["user"]["username"]
        )

        if self.type == "analysis":
            filtered_allele_ids = ih.get_filtered_alleles(
                self.type, self.id, interpretation["id"], filterconfig_id=self.filterconfig_id
            ).get_json()
            allele_ids = filtered_allele_ids["allele_ids"]
            excluded_allele_ids = filtered_allele_ids["excluded_allele_ids"]
        else:
            allele_ids = [self.id]
            excluded_allele_ids = {}

        r = ih.get_alleles(self.type, self.id, interpretation["id"], allele_ids)
        assert r.status_code == 200
        alleles = r.get_json()

        # Finalize all alleles
        annotation_ids = []
        custom_annotation_ids = []
        alleleassessment_ids = []
        allelereport_ids = []
        for allele_id in allele_ids:
            allele_assessment = next(
                aa for aa in allele_assessments if aa["allele_id"] == allele_id
            )
            allele_report = next(ar for ar in allele_reports if ar["allele_id"] == allele_id)
            allele_reference_assessments = [
                ra for ra in reference_assessments if ra["allele_id"] == allele_id
            ]
            allele = next(a for a in alleles if a["id"] == allele_id)
            annotation_id = allele["annotation"]["annotation_id"]
            annotation_ids.append(annotation_id)
            custom_annotation_id = (
                allele["annotation"]["custom_annotation_id"]
                if "custom_annotation_id" in allele["annotation"]
                else None
            )
            if custom_annotation_id:
                custom_annotation_ids.append(custom_annotation_id)
            ih.finalize_allele(
                self.type,
                self.id,
                allele_id,
                annotation_id,
                custom_annotation_id,
                allele_assessment,
                allele_report,
                allele_reference_assessments,
                interpretation["user"]["username"],
            )
            # Check that objects were created as they should
            (
                created_alleleassessment_id,
                created_allelereport_id,
                created_referenceassessment_ids,
            ) = self.check_finalize_allele(allele_id, interpretation)
            alleleassessment_ids.append(created_alleleassessment_id)
            allelereport_ids.append(created_allelereport_id)

        # Finalize workflow
        r = ih.finalize(
            self.type,
            self.id,
            allele_ids,
            annotation_ids,
            custom_annotation_ids,
            alleleassessment_ids,
            allelereport_ids,
            interpretation["user"]["username"],
            excluded_allele_ids=excluded_allele_ids,
        )

        assert r.status_code == 200

        interpretations = ih.get_interpretations(self.type, self.id).get_json()
        assert len(interpretations) == interpretation_cnt
        _assert_all_interpretations_are_done(interpretations)

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type, self.id, interpretation["id"]
        ).get_json()

        self._check_comments(reloaded_interpretation["state"], comment)

        assert reloaded_interpretation["finalized"] is True
        assert reloaded_interpretation["status"] == "Done"
        assert reloaded_interpretation["user"]["username"] == interpretation["user"]["username"]

    def perform_reopened_round(self, interpretation, comment):

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation["state"]["alleleassessments"]
        reference_assessments = interpretation["state"]["referenceassessments"]
        allele_reports = interpretation["state"]["allelereports"]

        # annotation is required for finalization
        annotations, custom_annotations = _build_dummy_annotations(
            [a["allele_id"] for a in allele_assessments]
        )

        if self.type == "analysis":
            filtered_allele_ids = ih.get_filtered_alleles(
                self.type, self.id, interpretation["id"], filterconfig_id=self.filterconfig_id
            ).get_json()
            allele_ids = filtered_allele_ids["allele_ids"]
            excluded_allele_ids = filtered_allele_ids["excluded_allele_ids"]
        else:
            allele_ids = [self.id]
            excluded_allele_ids = None

        assert set([a["allele_id"] for a in allele_assessments]) == set(allele_ids)
        assert set([a["allele_id"] for a in allele_reports]) == set(allele_ids)

        r = ih.get_alleles(self.type, self.id, interpretation["id"], allele_ids)
        assert r.status_code == 200
        alleles = r.get_json()

        # Finalize all alleles
        annotation_ids = []
        custom_annotation_ids = []
        alleleassessment_ids = []
        allelereport_ids = []
        for allele_id in allele_ids:
            allele = next(a for a in alleles if a["id"] == allele_id)
            # For a twist, only update allele report
            allele_assessment = next(
                aa for aa in allele_assessments if aa["allele_id"] == allele_id
            )
            allele_assessment.clear()
            allele_assessment["reuse"] = True
            allele_assessment["allele_id"] = allele_id
            allele_assessment["presented_alleleassessment_id"] = allele["allele_assessment"]["id"]

            allele_report = next(ar for ar in allele_reports if ar["allele_id"] == allele_id)
            allele_report["evaluation"]["comment"] = comment
            allele_report["presented_allelereport_id"] = allele["allele_report"]["id"]
            allele_reference_assessments = []
            for reference_assessment in reference_assessments:
                ra = next(
                    (
                        ra
                        for ra in allele["reference_assessments"]
                        if ra["allele_id"] == reference_assessment["allele_id"]
                        and ra["reference_id"] == reference_assessment["reference_id"]
                        and ra["allele_id"] == allele_id
                    ),
                    None,
                )
                if ra is None:
                    continue

                # Reuse reference assessment
                allele_reference_assessments.append(
                    {"id": ra["id"], "allele_id": allele_id, "reference_id": ra["reference_id"]}
                )

            annotation_id = allele["annotation"]["annotation_id"]
            annotation_ids.append(annotation_id)
            custom_annotation_id = (
                allele["annotation"]["custom_annotation_id"]
                if "custom_annotation_id" in allele["annotation"]
                else None
            )
            if custom_annotation_id:
                custom_annotation_ids.append(custom_annotation_id)
            ih.finalize_allele(
                self.type,
                self.id,
                allele_id,
                annotation_id,
                custom_annotation_id,
                allele_assessment,
                allele_report,
                allele_reference_assessments,
                interpretation["user"]["username"],
            )
            # Check that objects were created as they should
            (
                created_alleleassessment_id,
                created_allelereport_id,
                created_referenceassessment_ids,
            ) = self.check_finalize_allele(allele_id, interpretation)
            alleleassessment_ids.append(created_alleleassessment_id)
            allelereport_ids.append(created_allelereport_id)

        # Finalize workflow
        ih.save_interpretation_state(
            self.type, interpretation, self.id, interpretation["user"]["username"]
        )
        r = ih.finalize(
            self.type,
            self.id,
            allele_ids,
            annotation_ids,
            custom_annotation_ids,
            alleleassessment_ids,
            allelereport_ids,
            interpretation["user"]["username"],
            excluded_allele_ids=excluded_allele_ids,
        )
        assert r.status_code == 200

        interpretations = ih.get_interpretations(self.type, self.id).get_json()
        _assert_all_interpretations_are_done(interpretations)

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type, self.id, interpretation["id"]
        ).get_json()

        assert reloaded_interpretation["finalized"] is True
        assert reloaded_interpretation["status"] == "Done"
        assert reloaded_interpretation["user"]["username"] == interpretation["user"]["username"]
        assert all(
            ar["evaluation"]["comment"] == comment
            for ar in reloaded_interpretation["state"]["allelereports"]
        )

    def check_finalize_allele(self, allele_id, interpretation):

        # Check alleleassessment in database
        state_alleleassessment = next(
            a for a in interpretation["state"]["alleleassessments"] if a["allele_id"] == allele_id
        )
        allele_assessments_in_db = ih.get_allele_assessments_by_allele(allele_id).get_json()
        assert allele_assessments_in_db
        latest_allele_assessment = next(
            a for a in allele_assessments_in_db if not a["date_superceeded"]
        )
        if not state_alleleassessment.get("reuse"):
            assert (
                latest_allele_assessment["classification"]
                == state_alleleassessment["classification"]
            )
            assert (
                latest_allele_assessment["evaluation"]["comment"]
                == state_alleleassessment["evaluation"]["comment"]
            )
        else:
            assert (
                latest_allele_assessment["id"]
                == state_alleleassessment["presented_alleleassessment_id"]
            )

        # Check allelereport in database
        state_allelereport = next(
            a for a in interpretation["state"]["allelereports"] if a["allele_id"] == allele_id
        )
        allele_reports_in_db = ih.get_allele_reports_by_allele(allele_id).get_json()
        assert allele_reports_in_db
        latest_allele_report = next(a for a in allele_reports_in_db if not a["date_superceeded"])
        if not state_allelereport.get("reuse"):
            assert (
                latest_allele_report["evaluation"]["comment"]
                == state_allelereport["evaluation"]["comment"]
            )
        else:
            assert latest_allele_assessment["id"] == state_allelereport["presented_allelereport_id"]

        # Check on reference assessments:
        state_referenceassessments = [
            a
            for a in interpretation["state"]["referenceassessments"]
            if a["allele_id"] == allele_id
        ]
        result_reference_assessment_ids = []
        if state_referenceassessments:
            reference_assessments_in_db = ih.get_reference_assessments_by_allele(
                allele_id
            ).get_json()
            for state_referenceassessment in state_referenceassessments:
                matching_reference_assessment = next(
                    (
                        ra
                        for ra in reference_assessments_in_db
                        if ra["allele_id"] == allele_id
                        and ra["reference_id"] == state_referenceassessment["reference_id"]
                        and ra["date_superceeded"] is None
                    )
                )
                if "id" not in state_referenceassessment:
                    assert (
                        matching_reference_assessment["evaluation"]["comment"]
                        == state_referenceassessment["evaluation"]["comment"]
                    )
                else:
                    assert matching_reference_assessment["id"] == state_referenceassessment["id"]
                result_reference_assessment_ids.append(matching_reference_assessment["id"])
        return (
            latest_allele_assessment["id"],
            latest_allele_report["id"],
            result_reference_assessment_ids,
        )
