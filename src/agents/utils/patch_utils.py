"""Module: patch_utils.py — auto-generated docstring for flake8 friendliness."""

import logging
import os
import shutil
import subprocess
import time

logger = logging.getLogger("PatchUtils")
logging.basicConfig(
    level=logging.INFO, format="[PatchUtils] %(asctime)s %(levelname)s: %(message)s"
)

BACKUP_DIR = ".agent_backups"


def sanitize_patch_string(raw_patch: str) -> str:
    """Remove markdown fences and leading/trailing noise from LLM suggestions.

    - Strips triple backticks and optional language tags
    - Normalizes newlines to \n
    """
    txt = raw_patch.strip()
    # Strip triple backtick fences if present
    if txt.startswith("```") and txt.endswith("```"):
        # remove opening ```lang (optional) and trailing ```
        first_nl = txt.find("\n")
        if first_nl != -1:
            txt = txt[first_nl + 1 :]
        txt = txt[:-3]
    # Common ```patch or ```diff prefix in the first line
    if txt.lower().startswith("patch\n"):
        txt = txt[6:]
    txt = txt.replace("\r\n", "\n").replace("\r", "\n").strip()
    return txt


def backup_file(filepath: str):
    """
    Creates a backup of the specified file in a dedicated backup directory.

    Args:
        filepath (str): The path to the file to be backed up.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filepath))
    shutil.copy2(filepath, backup_path)
    logger.info(f"Backed up {filepath} to {backup_path}")
    return backup_path


def apply_patch(filepath: str, patch: str) -> bool:
    """Apply a unified diff patch to a file. Returns True if successful.

    Notes:
    - This expects a standard unified diff (---/+++ headers). We try multiple
      strategies: `patch` with -p0/-p1 and `git apply` as a fallback.
    - A backup is created before attempting to patch.
    """
    # Always take a backup first
    backup_file(filepath)
    # Quick escape: if the suggestion looks like a full-file replacement rather than a diff
    if not (patch.lstrip().startswith("---") or "diff --git" in patch):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(patch)
            logger.info(
                f"Wrote direct content update to {filepath} (non-diff suggestion)."
            )
            return True
        except Exception as e:
            logger.error(f"Failed writing direct update to {filepath}: {e}\n")
            return False

    # Write patch to a temporary file next to the target for easier relative paths
    import tempfile

    tmp_dir = os.path.dirname(os.path.abspath(filepath)) or "."
    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=tmp_dir, suffix=".patch", encoding="utf-8"
        ) as tf:
            tf.write(patch)
            patch_path = tf.name
    except Exception as e:
        logger.error(f"Unable to create temporary patch file: {e}")
        return False

    def _run(cmd: list[str]) -> tuple[bool, str]:
        try:
            proc = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True)
            ok = proc.returncode == 0
            out = (proc.stdout or "") + (proc.stderr or "")
            return ok, out
        except FileNotFoundError as e:
            return False, f"Command not found: {' '.join(cmd)} ({e})"
        except Exception as e:
            return False, f"Error running {' '.join(cmd)}: {e}"

    try:
        attempts: list[list[str]] = [
            ["patch", "--batch", "--forward", "-p0", "-i", patch_path],
            ["patch", "--batch", "--forward", "-p1", "-i", patch_path],
            ["git", "apply", "--reject", "--whitespace=fix", patch_path],
            ["git", "apply", "-p0", "--reject", "--whitespace=fix", patch_path],
        ]
        last_out = ""
        for idx, cmd in enumerate(attempts, start=1):
            ok, out = _run(cmd)
            last_out = out
            if ok:
                logger.info(f"Patched {filepath} successfully using: {' '.join(cmd)}")
                return True
            time.sleep(0.2 * idx)
        logger.error(
            f"All patch strategies failed for {filepath}. Output: {last_out[:1000]}"
        )
        # Persist last failure for diagnosis
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            with open(
                os.path.join(BACKUP_DIR, "last_patch_fail.log"), "w", encoding="utf-8"
            ) as lf:
                lf.write(last_out[:5000])
        except Exception:
            pass
        return False
    finally:
        try:
            os.remove(patch_path)
        except Exception:
            pass


def rollback_file(filepath: str):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filepath))
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filepath)
        logger.info(f"Rolled back {filepath} from {backup_path}")
        return True
    logger.warning(f"No backup found for {filepath}")
    return False


def apply_project_patch(patch: str) -> bool:
    """Apply a unified diff that may touch multiple files in the repository.

    Attempts `patch` first (-p0/-p1), then `git apply` as a fallback. Returns True on success.
    """
    import tempfile

    tmp_dir = os.getcwd()
    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=tmp_dir, suffix=".patch", encoding="utf-8"
        ) as tf:
            tf.write(patch)
            patch_path = tf.name
    except Exception as e:
        logger.error(f"Unable to create temporary patch file: {e}")
        return False

    def _run(cmd: list[str]) -> tuple[bool, str]:
        try:
            proc = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True)
            ok = proc.returncode == 0
            out = (proc.stdout or "") + (proc.stderr or "")
            return ok, out
        except FileNotFoundError as e:
            return False, f"Command not found: {' '.join(cmd)} ({e})"
        except Exception as e:
            return False, f"Error running {' '.join(cmd)}: {e}"

    try:
        attempts: list[list[str]] = [
            ["patch", "--batch", "--forward", "-p0", "-i", patch_path],
            ["patch", "--batch", "--forward", "-p1", "-i", patch_path],
            ["git", "apply", "--reject", "--whitespace=fix", patch_path],
            ["git", "apply", "-p0", "--reject", "--whitespace=fix", patch_path],
        ]
        last_out = ""
        for idx, cmd in enumerate(attempts, start=1):
            ok, out = _run(cmd)
            last_out = out
            if ok:
                logger.info("Project patch applied successfully.")
                return True
            time.sleep(0.2 * idx)
        logger.error(f"All project patch strategies failed. Output: {last_out[:1000]}")
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            with open(
                os.path.join(BACKUP_DIR, "last_project_patch_fail.log"),
                "w",
                encoding="utf-8",
            ) as lf:
                lf.write(last_out[:5000])
        except Exception:
            pass
        return False
    finally:
        try:
            os.remove(patch_path)
        except Exception:
            pass
