#!/usr/bin/env python3

""" Create a new Gitlab release for the given tag, including links to release artifacts and Docker image """

import argparse
import datetime
import subprocess
import sys
from dataclasses import dataclass, fields
from enum import Enum
from io import StringIO
from typing import Any, ClassVar, Dict, List, Optional, Tuple

import requests
from typing_extensions import Literal

# should be flexible enough to update these vars and work / require minimal changes to work on
# other projects/repos
gitlab_project = "alleles"
gitlab_repo = "ella"

# derived globals
url_root = f"https://gitlab.com/{gitlab_project}/{gitlab_repo}"
bucket_root = f"https://{gitlab_repo}.fra1.digitaloceanspaces.com/releases"
docker_root = f"registry.gitlab.com/{gitlab_project}/{gitlab_repo}"
# use url-encoded "alleles/ella" instead of specifying project/repo ID number
api_root = f"https://gitlab.com/api/v4/projects/{gitlab_project}%2F{gitlab_repo}"


### helper classes


class LinkType(str, Enum):
    other = "other"
    runbook = "runbook"
    image = "image"
    package = "package"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Link:
    name: str
    url: str
    # unadded links all have id -1
    id: int = -1
    link_type: LinkType = LinkType.other
    external: Optional[bool] = None
    filepath: Optional[str] = None

    # static class variable
    class_url: ClassVar[str] = f"{api_root}/releases/assets/links"

    @property
    def api_url(self) -> str:
        return f"{self.class_url}/{self.id}"

    def toJSON(self) -> Dict[str, str]:
        """Return a dict of strs for sending to gitlab API"""
        api_attrs = ["name", "url", "link_type", "filepath"]
        return {k: str(v) for k, v in self.__dict__.items() if k in api_attrs and v is not None}

    def save(self) -> "Link":
        """Create a link object on an existing release"""
        assert self.id == -1, f"Can't save an existing link, use old_link.update(new_link)"
        log(f"Adding new link for '{self.name}'")
        resp = requests.post(self.class_url, json=self.toJSON(), headers=headers)
        if resp.status_code != 201:
            error(f"Failed to add link: {resp.status_code} - {resp.json()['message']}")
            error(f"Link: {self}")
            exit(1)
        log(f"Link created successfully")
        return Link.from_api(resp.json())

    def update(self, new_link: "Link") -> "Link":
        """Update an existing link with new data"""
        log(f"Updating '{self.name}' with new data")
        new_data = {k: v for k, v in new_link.toJSON().items() if v != getattr(self, k)}
        resp = requests.put(self.api_url, json=new_data, headers=headers)
        if resp.status_code != 200:
            error(f"Failed to update link {new_link}")
            breakpoint()
            exit(1)
        log(f"Link updated successfully")
        return Link.from_api(resp.json())

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Link":
        """generate a Link object from API GET link response"""
        asset_root = f"{url_root}/-/releases/{args.tag}/downloads"

        if data.get("direct_asset_url"):
            if data["direct_asset_url"].startswith(asset_root):
                fpath = data["direct_asset_url"].replace(asset_root, "")
            elif data["url"] == data["direct_asset_url"]:
                fpath = data["url"][data["url"].rindex("/") :]
            else:
                error(f"Received unexpected link object: {data}")
                breakpoint()
                exit(1)
        else:
            fpath = None

        return cls(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            link_type=LinkType(data["link_type"]),
            external=data.get("external"),
            filepath=fpath,
        )


@dataclass(frozen=True)
class ReleaseAssets:
    links: List[Link]

    def __post_init__(self):
        assert len(self.links) > 0, f"Cannot instantiate empty link list"

    def toJSON(self) -> Dict[Literal["links"], List[Dict[str, str]]]:
        return {"links": [l.toJSON() for l in self.links]}


@dataclass(frozen=True)
class Release:
    tag_name: str
    id: int = -1
    name: Optional[str] = None
    description: Optional[str] = None
    ref: Optional[str] = None
    milestones: Optional[List[str]] = None
    assets: Optional[ReleaseAssets] = None
    created_at: Optional[datetime.datetime] = None
    released_at: Optional[datetime.datetime] = None

    # static class variables
    class_url: ClassVar[str] = f"{api_root}/releases"

    @property
    def api_url(self) -> str:
        return f"{self.class_url}/{self.id}"

    def toJSON(self) -> Dict[str, str]:
        """Return a dict of strs for sending to gitlab API"""
        api_attrs = ["name", "tag_name", "description", "ref", "milestones"]
        json_obj = {k: v for k, v in self.__dict__.items() if k in api_attrs and v is not None}
        if self.assets:
            json_obj["assets"] = self.assets.toJSON()
        if self.released_at:
            json_obj["released_at"] = self.released_at.isoformat()
        return json_obj

    def save(self) -> "Release":
        """Send API request to create Gitlab release"""
        assert (
            self.id == -1
        ), f"Cannot save an existing release, use old_release.update(new_release)"
        resp = requests.post(self.class_url, headers=headers, json=self.toJSON())
        if resp.status_code != 201:
            error(
                f"Error creating {args.tag} release: {resp.status_code} - {resp.json()['message']}"
            )
            breakpoint()
            exit(1)
        return self.from_api(resp.json())

    def update(self, new_release: "Release") -> "Release":
        """Updates an existing release"""
        raise NotImplementedError

    @classmethod
    def from_tag(cls, tag: str) -> "Release":
        """Get a Release object based on git tag"""
        resp = requests.get(f"{cls.class_url}/{tag}")
        if resp.status_code != 200:
            error(f"Failed to fetch release {tag}: {resp.status_code} - {resp.json()['message']}")
            breakpoint()
            exit(1)
        return cls.from_api(resp.json())

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Release":
        """Create Release object from API GET release response"""
        dt_fields = ["created_at", "released_at"]
        filtered_data: Dict[str, Any] = dict()
        field_names = [f.name for f in fields(cls)]

        for field_name, val in data.items():
            if field_name not in field_names:
                continue

            # handle special cases
            if field_name in dt_fields and val:
                # gitlab api gives not-quite-ISO format, so remove trailing Z
                val = datetime.datetime.fromisoformat(data[field_name][:-1])
            elif field_name == "assets" and val is not None and bool(val.get("links")):
                val = ReleaseAssets([Link.from_api(l) for l in val["links"]])
            filtered_data[field_name] = val
        return cls(**filtered_data)


### primary funcs


def main():
    log(f"Creating {args.tag} release on gitlab.com")
    release_notes = gen_release_notes()
    released_at = get_release_date()
    release_links = gen_links()

    log("Creating payload...")
    release = Release(
        description=release_notes,
        tag_name=args.tag,
        milestones=[args.tag],
        released_at=released_at,
        assets=release_links,
    )

    log("Sending to Gitlab")
    release.save()

    log("Done!")


def run_cmd(cmd: List) -> Tuple[str, str]:
    """Run a command (list), and return str output from stdout and stderr on success"""
    resp = subprocess.run(cmd, capture_output=True)
    if resp.returncode == 0:
        return resp.stdout.decode("UTF-8"), resp.stderr.decode("UTF-8")
    error(f"Got return code {resp.returncode} attempting to run: {' '.join(cmd)}")
    breakpoint()
    exit(1)


def gen_links() -> ReleaseAssets:
    """Generate Link objects for a new release"""
    # also fairly brittle when moving to another repo
    bucket = f"{bucket_root}/{args.tag}"
    src_name = f"{gitlab_repo}-release-{args.tag}-dist.tgz"
    sif_name = f"{gitlab_repo}-release-{args.tag}.sif"
    return ReleaseAssets(
        [
            Link(
                name=src_name,
                url=f"{bucket}/{src_name}",
                filepath=f"/{src_name}",
                link_type=LinkType.package,
            ),
            Link(
                name=sif_name,
                url=f"{bucket}/{sif_name}",
                filepath=f"/{sif_name}",
                link_type=LinkType.image,
            ),
        ]
    )


def gen_release_notes() -> str:
    """Generate release notes with docker image details and contents from existing docs"""
    # this is non-portable, so replace if using script with a diff repo
    notes_text = ["#### Docker Image\n\n", f"Docker image available: {docker_root}:{args.tag}\n\n"]

    stdout, _ = run_cmd(["git", "show", f"{args.tag}:docs/releasenotes/README.md"])
    skip_lines = True
    for line in StringIO(stdout):
        if line.startswith("### Highlights") and skip_lines:
            skip_lines = False
        elif line.startswith("## Version") and skip_lines is False:
            # only include most recent notes
            break

        if skip_lines is False:
            notes_text.append(
                line.replace(
                    "./img/",
                    f"https://gitlab.com/alleles/ella/raw/{args.tag}/docs/releasenotes/img/",
                )
            )
    return "".join(notes_text)


def get_release_date() -> datetime.datetime:
    """Get commit date on tag for release created_at"""
    dt_str, _ = run_cmd(["git", "log", "-1", "--format=%cI", args.tag])
    return datetime.datetime.fromisoformat(dt_str.strip())


### helper funcs


def log(msg: str, is_error: bool = False):
    if is_error:
        dest = sys.stderr
        msg = f"** ERROR **: {msg}"
    else:
        dest = sys.stdout
    print(f"{datetime.datetime.now()} - {msg}", file=dest)


def error(msg: str):
    log(msg, True)


###

if __name__ == "__main__":
    # use argparse for simplicity and free help text
    # args are global for convenience
    parser = argparse.ArgumentParser(
        description="adds / modifies asset links to an existing gitlab release"
    )
    parser.add_argument("api_key", metavar="GITLAB_API_TOKEN")
    parser.add_argument("tag", metavar="TAG_NAME")
    args = parser.parse_args()

    headers = {"Content-Type": "application/json", "PRIVATE-TOKEN": args.api_key}
    main()
