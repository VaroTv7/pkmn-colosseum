"""Plan original-asset extraction without requiring redundant FSYS archives.

A loose REL is not trusted merely because it exists: dtk validates its hash
against the unchanged module configuration during the normal split operation.
"""
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Union


def extraction_steps(
    version: str,
    archives: Mapping[str, Sequence[str]],
    root: Union[str, Path] = "orig",
) -> List[Dict[str, object]]:
    """Use an available archive, or accept its complete set of loose RELs.

    Missing input remains an explicit Ninja dependency, never a silent skip.
    If an archive is present, normal timestamp-based extraction is preserved.
    """
    files = Path(root) / version / "files"
    steps: List[Dict[str, object]] = []
    for archive, members in archives.items():
        if not members:
            raise ValueError(f"Archive {archive!r} has no configured members")
        source = files / archive
        outputs = [files / f"{member}.rel" for member in members]
        if not source.is_file() and all(path.is_file() for path in outputs):
            continue
        steps.append({
            "rule": "fsys_extract",
            "inputs": str(source),
            "implicit": [str(Path("tools") / "fsys_extract.py")],
            "outputs": [str(path) for path in outputs],
            "variables": {
                "members": " ".join(members),
                "out_dir": str(files),
            },
        })
    return steps
