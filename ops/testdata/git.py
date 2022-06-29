from __future__ import annotations

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
logger = logging.getLogger(Path(__file__).stem)
ROOT = Path(__file__).parents[2].absolute()
WORKING_DIR = Path().absolute()
COMMIT_HASH_RE = re.compile(r"[0-9a-f]")


class RefType(str, Enum):
    TAG = "tag"
    BRANCH = "branch"
    COMMIT = "commit"
    DEFAULT = "default"
    NOT_FOUND = "not found"


DETACHED_REFS = set([RefType.TAG, RefType.COMMIT])
# both branch and tag names are valid with `git clone --branch ...`
CLONE_TARGET_REFS = set([RefType.BRANCH, RefType.TAG])


@dataclass(frozen=True, repr=False)
class GitRef:
    type: RefType
    ref: Optional[str] = None

    def __post_init__(self):
        if not self.ref and self.type is not RefType.DEFAULT:
            raise ValueError(f"ref must be set for type {self.type}")
        elif self.ref and self.type is RefType.DEFAULT:
            raise ValueError("ref must be None for type DEFAULT")

    @property
    def is_detached(self) -> bool:
        return self.type in DETACHED_REFS

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ref='{self.ref}' type='{self.type}'>"

    def __str__(self) -> str:
        return f"{self.type}/{self.ref}"

    def matches(self, other: GitRef) -> bool:
        return (
            RefType.DEFAULT in [self.type, other.type]
            or self.type == other.type
            and self.ref == other.ref
        )


@dataclass(frozen=True)
class GitProcess:
    """subprocess.CompletedProcess, but with formatted output"""

    cwd: Optional[Path]
    args: Union[str, List[str]]
    returncode: int
    stdout: Optional[bytes]
    stderr: Optional[bytes]

    def _clean_bytes(self, bytestr: Optional[bytes], *, strip_chars: str = "\n") -> Optional[str]:
        if bytestr is None:
            return bytestr
        return bytestr.decode("UTF-8").strip(strip_chars)

    def output(self):
        return self._clean_bytes(self.stdout) or ""

    def output_lines(self):
        if not self.output():
            return []
        return self.output().splitlines()

    def error(self):
        return self._clean_bytes(self.stderr) or ""

    def error_lines(self):
        if not self.error():
            return []
        return self.error().splitlines()

    @classmethod
    def load(cls, proc: subprocess.CompletedProcess, *, cwd: Optional[Path] = None):
        if cwd is None:
            cwd = WORKING_DIR
        return cls(cwd=cwd, **vars(proc))


class Repository:
    __slots__ = ["repo_dir", "remote_url", "history", "offline"]
    repo_dir: Path
    remote_url: str
    history: List[GitProcess]
    offline: bool

    def __init__(
        self,
        repo_dir: Optional[Path] = None,
        remote_url: Optional[str] = None,
        *,
        offline: bool = False,
    ):
        self.history = []

        if repo_dir is None and remote_url is None:
            raise ValueError("You must specify at least one of: repo_dir, remote_url")
        elif repo_dir and not (repo_dir / ".git").exists() and remote_url is None:
            raise ValueError(f"{repo_dir}/.git does not exist and no remote_url specified")

        if repo_dir and remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = remote_url
        elif repo_dir and not remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = self.remote_get_url()
        elif remote_url and not repo_dir:
            self.remote_url = remote_url
            self.repo_dir = ROOT / url2reponame(self.remote_url)

        self.offline = offline or remote_url is None

    def __repr__(self):
        return f"<{self.__class__.__name__} repo_dir={self.repo_dir} remote_url={self.remote_url}>"

    @property
    def git_dir(self):
        return self.repo_dir / ".git"

    @property
    def sha(self) -> GitRef:
        return GitRef(RefType.COMMIT, self._commit_hash())

    @property
    def long_sha(self) -> GitRef:
        return GitRef(RefType.COMMIT, self._commit_hash(long=True))

    @property
    def ref(self) -> GitRef:
        return self.tag or self.branchname or self.sha

    @property
    def tag(self) -> Optional[GitRef]:
        cmd = "git tag -l --points-at HEAD".split()
        tag_name = self._exec(cmd).output()
        if tag_name:
            return GitRef(RefType.TAG, tag_name)
        return None

    @property
    def branchname(self) -> Optional[GitRef]:
        abbrev_ref = self._exec("git rev-parse --abbrev-ref HEAD").output()
        if abbrev_ref != "HEAD":
            return GitRef(RefType.BRANCH, abbrev_ref)
        return None

    def can_pull(self) -> bool:
        return not self.offline and not self.is_shallow()

    def _commit_hash(self, long: bool = False):
        cmd = "git rev-parse --short=8 HEAD".split()
        if long:
            cmd.remove("--short=8")
        proc = self._exec(cmd)
        commit_hash = proc.output()
        if not commit_hash:
            raise ValueError(f"Ran {' '.join(cmd)}, but got null output: {vars(proc)!r}")
        return commit_hash

    def _exec(
        self,
        cmd: Union[str, List[str]],
        *,
        check: bool = True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd: Optional[Path] = None,
        print_output: bool = False,
    ):
        if isinstance(cmd, str):
            cmd = cmd.split()
        cmd_str = " ".join(cmd)

        if not cwd:
            cwd = self.repo_dir

        if not cwd.exists():
            raise FileNotFoundError(f"Cannot execute '{cmd_str}', cwd does not exist: {cwd}")

        logger.debug(f"Executing: {cmd_str}")
        logger.debug(f"args: check={check} stdout={stdout} stderr={stderr} cwd={cwd}")
        try:
            proc = subprocess.run(cmd, check=check, stdout=stdout, stderr=stderr, cwd=cwd)
        except subprocess.CalledProcessError as e:
            out_str = e.output.decode("UTF-8").strip() if e.output else None
            err_str = e.stderr.decode("UTF-8").strip() if e.stderr else None
            logger.error(f"Error processing '{cmd_str}' in {cwd}")
            logger.error(f"stdout: {out_str}")
            logger.error(f"stderr: {err_str}")
            raise e
        logger.debug(f"Received: {proc!r}")

        git_proc = GitProcess.load(proc, cwd=cwd)
        if print_output:
            print(git_proc.output())
        self.history.append(git_proc)
        return git_proc

    ### Commands

    def checkout(self, ref: GitRef):
        "checks out the given ref (branch, sha, tag, etc.)"

        if self.is_shallow():
            bail(f"Cannot checkout {ref} from shallow repo {self!r}")
        elif self.offline:
            logger.warning(f"Checking out {ref} in offline mode, only using local worktree")
        else:
            cmd = f"git checkout {ref}".split()
            if ref.is_detached:
                cmd.insert(-1, "--detach")

            logger.info(f"Checking out {ref} (current: {self.ref})")
            try:
                return self._exec(cmd)
            except subprocess.CalledProcessError:
                err_msg = f"Checkout failed. "
                if self.is_shallow():
                    err_msg += f"Repo is in shallow mode. Verify ref exists and try again with --clean and --full to clone the repo with full history."
                else:
                    err_msg += f"Verify '{ref}' is a valid ref and try again."
                bail(err_msg)

    def clone(
        self,
        target: GitRef,
        *,
        depth: Optional[int] = None,
        force: bool = False,
    ):
        if self.offline:
            bail(f"Cannot clone new data in offline mode")
        elif target.type is RefType.COMMIT and depth:
            bail(f"Cannot shallow clone to a commit hash, use a tag or branch instead")

        if self.git_dir.exists():
            if not force:
                raise FileExistsError(f"Repo already exists at {self.repo_dir}")
            logging.info(f"Removing existing data from {self.repo_dir}")
            self.reset_repo(keep_dir=True)

        cmd = ["git", "clone"]
        if depth:
            cmd += [f"--depth={depth}"]
        cmd += [self.remote_url, str(self.repo_dir)]

        if target.type in CLONE_TARGET_REFS:
            cmd += [f"--branch={target.ref}"]

        logger.info(f"Cloning {self.remote_url} to {self.repo_dir} using ref {target}")
        res = [self._exec(cmd, cwd=WORKING_DIR)]

        # can't clone directly to a commit hash, so do a full clone and then checkout
        if target.type is RefType.COMMIT:
            res.append(self.checkout(target))

        return res

    def fetch(self):
        logger.info(f"Running git fetch with {self.remote_url}")
        return self._exec("git fetch", print_output=True)

    def pull(self):
        if self.is_shallow():
            logger.info(f"Shallow repo and data already fetched, nothing to do")
        elif self.offline:
            logger.warning(f"Running in offline mode, using existing data from {self.ref}")
        else:
            logger.info(f"Running git pull on {self.ref}")
            return self._exec("git pull", print_output=True)

    def remote_get_url(self, remote_name: str = "origin"):
        return self._exec(f"git remote get-url {remote_name}").output()

    ### Helpers

    def is_clean(self):
        return not self._exec("git status -s").output().strip()

    def is_shallow(self):
        return (self.git_dir / "shallow").exists()

    def is_valid_commit(self, val: str):
        if not self.git_dir:
            raise FileNotFoundError(f"No local repo found at {self.repo_dir}, cannot check commit")
        cmd = f"git branch -a --contains {val}".split()
        proc = self._exec(cmd, check=False)
        if proc.returncode == 0:
            return True
        elif proc.returncode == 129:
            return False
        else:
            raise RuntimeError(f"Git command failed unexpectedly: {proc!r}")

    def find_ref(self, val: str) -> GitRef:
        ref_type = self.ref_type(val)
        return GitRef(type=ref_type, ref=val)

    def remote_ref_exists(self, ref_name: str):
        """checks if the ref (branch, tag, etc.) exists in the remote repo"""
        try:
            return self._lookup_ref(ref_name).returncode == 0
        except subprocess.CalledProcessError:
            return False

    def ref_type(self, ref_name: str) -> RefType:
        if not self.git_dir.exists() or self.is_shallow():
            if self.offline:
                raise FileNotFoundError(
                    f"Repo dir not found, cannot perform offline ref lookup: {self.repo_dir}"
                )
            ls_remote = self._exec(
                f"git ls-remote --heads --tags {self.remote_url}",
                check=False,
                cwd=WORKING_DIR,
            )

            if f"refs/tags/{ref_name}" in ls_remote.output():
                return RefType.TAG
            elif f"refs/heads/{ref_name}" in ls_remote.output():
                return RefType.BRANCH
            elif any(l.startswith(ref_name) for l in ls_remote.output().splitlines()):
                # only present if the hash is the head of a branch
                return RefType.COMMIT
            elif is_hash(ref_name):
                # the output from ls-remote only shows hashes from the HEAD of each branch/tag.
                # Since there is not a local repo to check the full history, we can assume that
                # the hash is a commit if it matches the hash regex. If the commit does not
                # exist, an exception will be raised when we try to check it out.
                return RefType.COMMIT
        else:
            if self.offline:
                ref_cmd = "rev-parse --verify --quiet"
            else:
                ref_cmd = "fetch origin --quiet"

            if self._exec(f"git {ref_cmd} refs/tags/{ref_name}", check=False).returncode == 0:
                return RefType.TAG
            elif self._exec(f"git {ref_cmd} refs/heads/{ref_name}", check=False).returncode == 0:
                return RefType.BRANCH
            elif (
                self._exec(f"git rev-parse --verify {ref_name}^{{commit}}", check=False).returncode
                == 0
            ):
                return RefType.COMMIT

        if is_hash(ref_name) and self.is_shallow():
            logger.warning(
                f"'{ref_name}' matches the hash regex, but has not been found in the shallow repo. It may exist in the full repo."
            )
        return RefType.NOT_FOUND

    def reset_repo(self, *, keep_dir: bool = False):
        logger.info(f"Removing local repo data from {self.repo_dir}")
        if keep_dir:
            for f in self.repo_dir.iterdir():
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    f.unlink()
        else:
            shutil.rmtree(self.repo_dir)

    def _lookup_ref(self, ref_name: str):
        if self.offline:
            cmd = f"git show-ref {ref_name}".split()
        else:
            cmd = f"git ls-remote --exit-code {self.remote_url} {ref_name}".split()
        return self._exec(cmd, cwd=WORKING_DIR)


def url2reponame(url: str):
    return url.rsplit("/", 1)[-1].replace(".git", "")


def is_hash(val: str):
    if COMMIT_HASH_RE.match(val):
        if len(val) in [7, 8, 40]:
            return True
    return False


def bail(msg: str):
    logger.error(msg)
    exit(1)
