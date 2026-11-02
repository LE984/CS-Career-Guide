"""Manually copy the old vector store to a new dimension without a MySQL connection."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from cs_career_guide.vector_store import DEFAULT_EMBEDDING_DIMENSION, migrate_career_store


def main():
    backend_dir = Path(__file__).resolve().parent
    load_dotenv(backend_dir / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=backend_dir / "ai_integration/lancedb")
    parser.add_argument("--destination", type=Path, required=True, help="New directory; never overwrites an existing table")
    parser.add_argument("--dimension", type=int, default=int(os.getenv("EMBEDDING_DIMENSION", DEFAULT_EMBEDDING_DIMENSION)))
    args = parser.parse_args()
    try:
        report = migrate_career_store(args.source, args.destination, args.dimension)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
