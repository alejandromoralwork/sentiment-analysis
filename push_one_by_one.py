from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List


DEFAULT_SKIP_PARTS = {
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}

DEFAULT_SKIP_NAMES = {
    "*.pyc",
    "*.log",
    "warn-*.txt",
}


def run_git(args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        capture_output=capture_output,
    )


def in_git_repo() -> bool:
    try:
        run_git(["rev-parse", "--is-inside-work-tree"], capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def tune_git_for_slow_links() -> None:
    # These settings help with slow or flaky HTTP remotes.
    for config_args in (
        ["config", "--global", "http.version", "HTTP/1.1"],
        ["config", "--global", "http.lowSpeedLimit", "0"],
        ["config", "--global", "http.lowSpeedTime", "999999"],
    ):
        try:
            run_git(config_args)
        except subprocess.CalledProcessError:
            # If the environment blocks global config writes, continue anyway.
            pass


def collect_changed_files() -> List[str]:
    changed: List[str] = []

    try:
        diff = run_git(["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"], capture_output=True)
        changed.extend(line.strip() for line in diff.stdout.splitlines() if line.strip())
    except subprocess.CalledProcessError:
        pass

    try:
        untracked = run_git(["ls-files", "--others", "--exclude-standard"], capture_output=True)
        changed.extend(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    except subprocess.CalledProcessError:
        pass

    # Keep unique files while preserving order.
    seen = set()
    result: List[str] = []
    for file_name in changed:
        normalized = file_name.replace("\\", "/")
        if normalized not in seen:
            seen.add(normalized)
            result.append(file_name)
    return result


def get_current_branch() -> str:
    completed = run_git(["branch", "--show-current"], capture_output=True)
    branch = completed.stdout.strip()
    return branch or "main"


def should_skip(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")

    if any(part in DEFAULT_SKIP_PARTS for part in parts):
        return True

    name = Path(normalized).name.lower()
    if name.endswith(".pyc"):
        return True
    if name.endswith(".log"):
        return True
    if name.startswith("warn-") and name.endswith(".txt"):
        return True

    return False


def build_commit_message(path: str, prefix: str) -> str:
    name = Path(path).name
    return f"{prefix}: {name}"


def looks_like_non_fast_forward(error: subprocess.CalledProcessError) -> bool:
    message = ""
    if error.stderr:
        message += error.stderr.lower()
    if error.stdout:
        message += "\n" + error.stdout.lower()

    return any(
        marker in message
        for marker in (
            "non-fast-forward",
            "tip of your current branch is behind",
            "fetch first",
            "rejected",
        )
    )


def fetch_and_rebase(remote: str, branch: str) -> bool:
    try:
        print(f"Fetching {remote}/{branch}...")
        run_git(["fetch", remote, branch])
        print(f"Rebasing onto {remote}/{branch}...")
        run_git(["rebase", f"{remote}/{branch}"])
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Rebase failed: {exc}")
        return False


def stage_commit_push(
    paths: Iterable[str],
    force_with_lease: bool,
    force: bool,
    dry_run: bool,
    prefix: str,
    remote: str,
    branch: str,
    retries: int,
    retry_delay: float,
) -> int:
    pushed = 0
    failures = 0

    for path in paths:
        print(f"\n==> {path}")

        if dry_run:
            print(f"[dry-run] git add -- {path}")
            print(f"[dry-run] git commit -m \"{build_commit_message(path, prefix)}\"")
            print("[dry-run] git push")
            pushed += 1
            continue

        try:
            run_git(["add", "--", path])
            run_git(["commit", "-m", build_commit_message(path, prefix)])
        except subprocess.CalledProcessError as exc:
            # Common case: nothing changed after staging or file is already committed.
            print(f"Skip/commit failed for {path}: {exc}")
            failures += 1
            continue

        push_args = ["push"]
        if force_with_lease:
            push_args.append("--force-with-lease")
        elif force:
            push_args.append("--force")
        push_args.extend([remote, f"HEAD:{branch}"])

        push_success = False
        for attempt in range(1, retries + 1):
            try:
                run_git(push_args)
                push_success = True
                pushed += 1
                break
            except subprocess.CalledProcessError as exc:
                print(f"Push failed for {path} (attempt {attempt}/{retries}): {exc}")

                if looks_like_non_fast_forward(exc):
                    print("Remote is ahead. Trying fetch + rebase before retrying...")
                    if fetch_and_rebase(remote, branch):
                        continue

                if attempt < retries:
                    sleep_seconds = retry_delay * attempt
                    print(f"Retrying in {sleep_seconds:.1f}s...")
                    time.sleep(sleep_seconds)

        if not push_success:
            failures += 1
            continue

    print(f"\nDone. Successful files: {pushed}, failed: {failures}")
    return 0 if failures == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage, commit, and push changed files one by one to keep uploads small."
    )
    parser.add_argument(
        "--force-with-lease",
        action="store_true",
        help="Use git push --force-with-lease instead of a normal push.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Use git push --force. Safer to use --force-with-lease instead.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without changing git history.",
    )
    parser.add_argument(
        "--prefix",
        default="Update",
        help="Commit message prefix. Default: Update",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote name to push to. Default: origin",
    )
    parser.add_argument(
        "--branch",
        default="",
        help="Target branch name. Default: current branch.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of push attempts per file. Default: 3",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=5.0,
        help="Base delay in seconds between push retries. Default: 5",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not in_git_repo():
        print("Error: this script must be run inside a git repository.")
        return 1

    tune_git_for_slow_links()

    files = collect_changed_files()
    files = [path for path in files if not should_skip(path)]

    if not files:
        print("No changed files found after filtering.")
        return 0

    branch = args.branch or get_current_branch()

    print("Changed files to process:")
    for file_name in files:
        print(f"  {file_name}")

    print(f"Using remote '{args.remote}' and branch '{branch}'")

    if not args.force and not args.force_with_lease:
        print("Default push mode: force-with-lease.")
        args.force_with_lease = True

    if args.force:
        print("Warning: using --force can overwrite remote history.")

    return stage_commit_push(
        files,
        force_with_lease=args.force_with_lease,
        force=args.force,
        dry_run=args.dry_run,
        prefix=args.prefix,
        remote=args.remote,
        branch=branch,
        retries=max(1, args.retries),
        retry_delay=max(0.0, args.retry_delay),
    )


if __name__ == "__main__":
    raise SystemExit(main())
