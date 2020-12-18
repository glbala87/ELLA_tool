import pytest
from vardb.datamodel import gene, user


class TestGenepanel(object):
    @pytest.mark.ca(order=0)
    def test_create_new(self, test_database, client, session):
        test_database.refresh()  # Reset db

        r = client.get("/api/v1/genepanels/")
        r = client.get("/api/v1/genepanels/{name}/{version}/".format(**r.get_json()[0]))
        genepanel_to_copy = r.get_json()

        original_name = genepanel_to_copy["name"]
        original_version = genepanel_to_copy["version"]

        genepanel_to_copy["name"] = "NewPanel"
        genepanel_to_copy["version"] = "NewVersion"
        genepanel_to_copy["usergroups"] = ["testgroup01", "testgroup02"]
        r = client.post("/api/v1/genepanels/", genepanel_to_copy)
        assert r.status_code == 200

        # Check that panel is correctly created
        original = (
            session.query(gene.Genepanel)
            .filter(
                gene.Genepanel.name == original_name, gene.Genepanel.version == original_version
            )
            .one()
        )

        created = (
            session.query(gene.Genepanel)
            .filter(
                gene.Genepanel.name == genepanel_to_copy["name"],
                gene.Genepanel.version == genepanel_to_copy["version"],
            )
            .one()
        )

        original_phenotype_ids = [p.id for p in original.phenotypes]
        created_phenotype_ids = [p.id for p in created.phenotypes]
        assert set(original_phenotype_ids) == set(created_phenotype_ids)

        original_transcript_ids = [p.id for p in original.transcripts]
        created_transcript_ids = [p.id for p in created.transcripts]
        assert set(original_transcript_ids) == set(created_transcript_ids)

        assert created.name == genepanel_to_copy["name"]
        assert created.version == genepanel_to_copy["version"]

        # Check that groups are correct
        original_usergroups = (
            session.query(user.UserGroup.name)
            .join(
                user.UserGroupGenepanel, user.UserGroupGenepanel.c.usergroup_id == user.UserGroup.id
            )
            .filter(
                user.UserGroupGenepanel.c.genepanel_name == original_name,
                user.UserGroupGenepanel.c.genepanel_version == original_version,
            )
        ).scalar_all()

        assert set(original_usergroups) == set(["testgroup01", "testgroup03"])

        created_usergroups = (
            session.query(user.UserGroup.name)
            .join(
                user.UserGroupGenepanel, user.UserGroupGenepanel.c.usergroup_id == user.UserGroup.id
            )
            .filter(
                user.UserGroupGenepanel.c.genepanel_name == genepanel_to_copy["name"],
                user.UserGroupGenepanel.c.genepanel_version == genepanel_to_copy["version"],
            )
        ).scalar_all()

        assert set(created_usergroups) == set(genepanel_to_copy["usergroups"])

        # Check testgroup01 not allowed to import to testgroup03
        genepanel_to_copy["name"] = "NewPanel2"
        genepanel_to_copy["version"] = "NewVersion2"
        genepanel_to_copy["usergroups"] = ["testgroup01", "testgroup03"]
        with pytest.raises(AssertionError):
            r = client.post("/api/v1/genepanels/", genepanel_to_copy)
            assert r.status_code == 200
