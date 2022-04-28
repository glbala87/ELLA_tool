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
    HEAD = "head"
    NOT_FOUND = "not found"


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
        return self.output().split("\n")

    def error(self):
        return self._clean_bytes(self.stderr) or ""

    def error_lines(self):
        if not self.error():
            return []
        return self.error().split("\n")

    @classmethod
    def load(cls, proc: subprocess.CompletedProcess, *, cwd: Optional[Path] = None):
        if cwd is None:
            cwd = Path().absolute()
        return cls(cwd=cwd, **vars(proc))


class Repository:
    repo_dir: Path
    remote_url: str
    history: List[GitProcess]

    def __init__(self, repo_dir: Optional[Path] = None, remote_url: Optional[str] = None):
        self.history = []

        if repo_dir is None and remote_url is None:
            raise ValueError("You must specify at least one of: repo_dir, remote_url")
        elif repo_dir and not repo_dir.exists() and remote_url is None:
            raise ValueError("repo_dir does not exist and no remote_url specified")

        if repo_dir and remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = remote_url
        elif repo_dir and not remote_url:
            self.repo_dir = repo_dir.absolute()
            self.remote_url = self.remote_get_url()
        elif remote_url and not repo_dir:
            self.remote_url = remote_url
            self.repo_dir = ROOT / url2reponame(self.remote_url)

    def __repr__(self):
        return f"<{self.__class__.__name__} repo_dir={self.repo_dir} remote_url={self.remote_url}>"

    @property
    def git_dir(self):
        return self.repo_dir / ".git"

    @property
    def sha(self):
        return self._commit_hash()

    @property
    def long_sha(self):
        return self._commit_hash(long_hash=True)

    @property
    def ref(self):
        return self.tag or self.branchname or self.sha

    @property
    def tag(self):
        cmd = "git tag -l --points-at HEAD".split()
        return self._exec(cmd).output() or None

    @property
    def branchname(self):
        abbrev_ref = self._exec("git rev-parse --abbrev-ref HEAD").output()
        return None if abbrev_ref == "HEAD" else abbrev_ref

    def _commit_hash(self, long_hash: bool = False):
        cmd = "git rev-parse HEAD".split()
        if not long_hash:
            cmd.insert(-1, "--short=8")
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

        if not cwd:
            cwd = self.repo_dir

        logger.debug(f"Executing: {' '.join(cmd)}")
        logger.debug(f"args: check={check} stdout={stdout} stderr={stderr} cwd={cwd}")
        try:
            proc = subprocess.run(cmd, check=check, stdout=stdout, stderr=stderr, cwd=cwd)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing {' '.join(cmd)} in {cwd}")
            logger.error(f"stdout: {e.output}")
            logger.error(f"stderr: {e.stderr}")
            raise e
        logger.debug(f"Received: {proc!r}")

        git_proc = GitProcess.load(proc, cwd=cwd)
        if print_output:
            print(git_proc.output())
        self.history.append(git_proc)
        return git_proc

    ### Commands

    def checkout(self, ref: str, *, detached: bool = True):
        "checks out the given ref (branch, sha, tag, etc.)"
        cmd = f"git checkout {ref}".split()
        if detached:
            cmd.insert(-1, "--detach")
        self._exec(cmd)
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

        cmd = ["git", "clone"]
        if branchname:
            cmd += [f"--branch={branchname}"]
        if depth is not None:
            cmd += [f"--depth={depth}"]
        cmd += [self.remote_url, str(self.repo_dir)]

        logger.info(f"Cloning {self.remote_url} to {self.repo_dir}")
        self._exec(cmd, cwd=self.repo_dir.parent)
        return self

    def fetch(self):
        self._exec("git fetch", print_output=True)
        return self

    def pull(self):
        self._exec("git pull", print_output=True)
        return self

    def remote_get_url(self, remote_name: str = "origin"):
        return self._exec(f"git remote get-url {remote_name}").output()

    ### Helpers

    def is_clean(self):
        proc = self._exec("git status -s")
        return not proc.output().strip()

    def is_shallow(self):
        return (self.git_dir / "shallow").exists()

    def is_valid_commit(self, val: str):
        cmd = f"git branch -a --contains {val}".split()
        proc = self._exec(cmd, check=False)
        if proc.returncode == 0:
            return True
        elif proc.returncode == 129:
            return False
        else:
            raise RuntimeError(f"Git command failed unexpectedly: {proc!r}")

    def remote_ref_exists(self, ref_name: str):
        """checks if the ref (branch, tag, etc.) exists in the remote repo"""
        try:
            return self._lookup_ref(ref_name).returncode == 0
        except subprocess.CalledProcessError:
            return False

    def ref_type(self, ref_name: str, offline: bool = False) -> RefType:
        if offline:
            ref_cmd = "rev-parse --verify --quiet"
        else:
            ref_cmd = "fetch origin --quiet"

        if self._exec(f"git {ref_cmd} refs/tags/{ref_name}", check=False).returncode == 0:
            return RefType.TAG
        elif self._exec(f"git {ref_cmd} refs/heads/{ref_name}", check=False).returncode == 0:
            return RefType.BRANCH
        elif (
            self._exec(f"git rev-parse --verify {ref_name}^{{commit}}", check=False).returncode == 0
        ):
            return RefType.COMMIT

        return RefType.NOT_FOUND

    def _lookup_ref(self, ref_name: str, offline: bool = False):
        if offline:
            cmd = f"git show-ref {ref_name}".split()
        else:
            cmd = f"git ls-remote --exit-code {self.remote_url} {ref_name}".split()
        return self._exec(cmd, cwd=Path())


def url2reponame(url: str):
    return url.rsplit("/", 1)[-1].replace(".git", "")


def is_hash(val: str):
    if COMMIT_HASH_RE.match(val):
        if len(val) in [7, 8, 40]:
            return True
    return False
