import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
StrPath = Union[str, Path]
ROOT = Path(__file__).parents[2].absolute()
COMMIT_HASH_RE = re.compile(r"[0-9a-f]")


class RefType(str, Enum):
    TAG = "tag"
    BRANCH = "branch"
    COMMIT = "commit"
    NOT_FOUND = "not found"


@dataclass(frozen=True)
class GitProcess:
    """subprocess.CompletedProcess, but with formatted output"""

    args: Union[str, List[str]]
    returncode: int
    stdout: Optional[bytes]
    stderr: Optional[bytes]

    def output(self):
        if self.stdout:
            return self.stdout.decode().strip("\n")
        return ""

    def output_lines(self):
        if self.output():
            return self.output().split("\n")
        return []


class Repository:
    __slots__ = ["repo_dir", "remote_url"]
    repo_dir: Path
    remote_url: str

    def __init__(self, repo_dir: Optional[Path] = None, remote_url: Optional[str] = None):
        if repo_dir is None and remote_url is None:
            raise ValueError("You must specify at least one of: repo_dir, remote_url")
        elif repo_dir and not repo_dir.exists() and remote_url is None:
            raise ValueError("repo_dir does not exist and no remote_url specified")

        if repo_dir and remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = remote_url
        elif repo_dir and not remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = self.get_repo_remote_url(self.repo_dir)
        elif remote_url and not repo_dir:
            self.remote_url = remote_url
            self.repo_dir = ROOT / url2reponame(self.remote_url)

    def __repr__(self):
        return f"<{self.__class__.__name__} repo_dir={self.repo_dir} remote_url={self.remote_url}>"

    @property
    def sha(self):
        return self._commit_hash()

    @property
    def long_sha(self):
        return self._commit_hash(long_hash=True)

    @property
    def ref(self):
        if self.tag:
            return self.tag
        elif self.branchname == "HEAD":
            return self.long_sha
        else:
            return self.branchname

    @property
    def tag(self):
        cmd = "git tag -l --points-at HEAD".split()
        return git_exec(cmd, cwd=self.repo_dir).output() or None

    def _commit_hash(self, long_hash: bool = False):
        cmd = "git rev-parse HEAD".split()
        if not long_hash:
            cmd.insert(-1, "--abbrev=8")
        proc = git_exec(cmd, cwd=self.repo_dir)
        commit_hash = proc.output()
        if not commit_hash:
            raise ValueError(f"Ran {' '.join(cmd)}, but got null output: {vars(proc)!r}")
        return commit_hash

    @property
    def branchname(self):
        cmd = "git rev-parse --abbrev-ref HEAD".split()
        return git_exec(cmd, cwd=self.repo_dir).output()

    def is_clean(self):
        r = subprocess.check_output(f"git status -s".split())
        return not bool(r)

    def remote_ref_exists(self, ref_name: str):
        """checks if the ref (branch, tag, etc.) exists in the remote repo"""
        try:
            return self._lookup_ref(ref_name).returncode == 0
        except subprocess.CalledProcessError:
            return False

    def ref_type(self, ref_name: str) -> RefType:
        if self.remote_ref_exists(ref_name):
            proc = self._lookup_ref(ref_name)
            ref_path = proc.output().split("\t")[-1]
            if ref_path.startswith("refs/heads/"):
                return RefType.BRANCH
            elif ref_path.startswith("refs/tags/"):
                return RefType.TAG
            else:
                raise ValueError(
                    f"Cannot determine ref type of {ref_name} with git output: '{proc.output()}'"
                )
        elif is_hash(ref_name) and self.is_valid_commit(ref_name):
            return RefType.COMMIT
        else:
            return RefType.NOT_FOUND

    def _lookup_ref(self, ref_name: str):
        cmd = f"git ls-remote --exit-code {self.remote_url} {ref_name}".split()
        return git_exec(cmd)

    def is_valid_commit(self, val: str):
        cmd = f"git branch -a --contains {val}".split()
        proc = git_exec(cmd, cwd=self.repo_dir, check=False)
        if proc.returncode == 0:
            return True
        elif proc.returncode == 129:
            return False
        else:
            raise RuntimeError(f"Git command failed unexpectedly: {proc!r}")

    ### Commands

    def checkout(self, ref: str, *, detached: bool = True):
        "checks out the given ref (branch, sha, tag, etc.)"
        cmd = f"git checkout {ref}".split()
        if detached:
            cmd.insert(-1, "--detach")
        git_exec(cmd, cwd=self.repo_dir)
        return self

    def clone(
        self,
        *,
        branchname: Optional[str] = None,
        depth: Optional[int] = None,
        force: bool = False,
    ):
        if self.repo_dir.exists():
            if not force:
                raise FileExistsError(f"Repo already exists at {self.repo_dir}")
            logging.info(f"Removing existing data from {self.repo_dir}")
            shutil.rmtree(self.repo_dir)

        cmd = "git clone".split()
        if branchname:
            cmd.append(f"--branch={branchname}")
        if depth is not None:
            cmd.append(f"--depth={depth}")
        cmd.extend([self.remote_url, str(self.repo_dir)])
        logger.info(f"Cloning {self.remote_url} to {self.repo_dir}")
        git_exec(cmd)
        return self

    ### Convenience functions

    @staticmethod
    def get_repo_remote_url(repo_dir: Path):
        cmd = "git remote get-url origin".split()
        return git_exec(cmd, cwd=repo_dir).output()


def url2reponame(url: str):
    return url.rsplit("/", 1)[-1].replace(".git", "")


def is_hash(val: str):
    if COMMIT_HASH_RE.match(val):
        if len(val) in [7, 8, 40]:
            return True
    return False


def git_exec(
    cmd: List[str],
    *,
    check: bool = True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd: Optional[Path] = None,
):
    logger.debug(f"Executing: {' '.join(cmd)}")
    logger.debug(f"args: check={check} stdout={stdout} stderr={stderr} cwd={cwd}")
    proc = subprocess.run(cmd, check=check, stdout=stdout, stderr=stderr, cwd=cwd)
    logger.debug(f"Received: {proc!r}")
    return GitProcess(**vars(proc))
