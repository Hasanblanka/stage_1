"""Download the pinned Stage 1 dataset and create canonical JSONL."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml
from huggingface_hub import HfApi, hf_hub_download

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polygraf_ner.io import (  # noqa: E402
    normalize_json_value,
    sha256_file,
    write_json,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "project.yaml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    stage = config["stage1"]
    source = stage["source"]
    output_dir = REPO_ROOT / stage["raw_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    info = api.dataset_info(
        source["repo_id"],
        revision=source["revision"],
        files_metadata=True,
    )
    if info.sha != source["revision"]:
        raise RuntimeError(
            f"Resolved revision {info.sha} does not match pin {source['revision']}"
        )

    filenames = [source["split_file"], "README.md", "LICENSE"]
    local_files: dict[str, Path] = {}
    for filename in filenames:
        cached_path = Path(
            hf_hub_download(
                repo_id=source["repo_id"],
                filename=filename,
                repo_type="dataset",
                revision=source["revision"],
            )
        )
        destination = output_dir / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached_path, destination)
        local_files[filename] = destination

    dataframe = pd.read_parquet(local_files[source["split_file"]])
    records = [
        normalize_json_value(record)
        for record in dataframe.to_dict(orient="records")
    ]
    if len(records) != stage["expected_records"]:
        raise RuntimeError(
            f"Expected {stage['expected_records']} records, found {len(records)}"
        )

    jsonl_path = output_dir / "starter_100.jsonl"
    write_jsonl(records, jsonl_path)

    manifest = {
        "repo_id": source["repo_id"],
        "requested_revision": source["revision"],
        "resolved_revision": info.sha,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": len(records),
        "files": {
            str(path.relative_to(output_dir)).replace("\\", "/"): {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in [*local_files.values(), jsonl_path]
        },
    }
    write_json(manifest, output_dir / "manifest.json")
    print(
        f"Downloaded {len(records)} records from {source['repo_id']}@{info.sha}"
    )
    print(f"Canonical JSONL: {jsonl_path}")


if __name__ == "__main__":
    main()
