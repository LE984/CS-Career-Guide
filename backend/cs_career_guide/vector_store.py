"""One schema and dimension contract for all career recommendation writers."""

DEFAULT_EMBEDDING_DIMENSION = 512
DEFAULT_LANCEDB_RELATIVE_PATH = "../.runtime/lancedb"
CAREER_TABLE_NAME = "career_recommendations"


def career_schema(dimension):
    import pyarrow as pa

    return pa.schema([
        ("id", pa.string()),
        ("user_id", pa.string()),
        ("self_introduction", pa.string()),
        ("introduction_preview", pa.string()),
        ("recommendations", pa.string()),
        ("analysis_result", pa.string()),
        ("created_at", pa.string()),
        # Missing embeddings are null, never fabricated by padding or truncation.
        ("embedding", pa.list_(pa.float32(), dimension)),
    ])


def validate_embedding(vector, dimension):
    import math

    if vector is None:
        return None
    values = [float(value) for value in vector]
    if len(values) != dimension:
        raise ValueError(f"Embedding has {len(values)} dimensions; expected {dimension}")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Embedding contains non-finite values")
    return values


def validate_model_dimension(model, dimension):
    actual = model.get_sentence_embedding_dimension()
    if actual != dimension:
        raise ValueError(
            f"Model outputs {actual} dimensions, but EMBEDDING_DIMENSION={dimension}. "
            "Use a matching model and migrate the vector store before changing dimensions."
        )


def career_record(data, dimension):
    import json

    row = {
        name: data.get(name, "")
        for name in career_schema(dimension).names
        if name != "embedding"
    }
    if isinstance(row["recommendations"], (list, dict)):
        row["recommendations"] = json.dumps(row["recommendations"], ensure_ascii=False)
    row["embedding"] = validate_embedding(data.get("embedding"), dimension)
    return row


def open_career_table(db, dimension):
    if CAREER_TABLE_NAME not in db.table_names():
        return db.create_table(CAREER_TABLE_NAME, schema=career_schema(dimension))
    table = db[CAREER_TABLE_NAME]
    expected = career_schema(dimension)
    actual = table.schema
    if any(name not in actual.names or actual.field(name).type != expected.field(name).type for name in expected.names):
        raise ValueError(
            f"Career vector table schema does not match {dimension} dimensions. "
            "Run backend/migrate_vector_store.py to copy and migrate the old store safely."
        )
    return table


def migrate_career_store(source_path, destination_path, dimension):
    """Copy a legacy store into a new directory without changing the source."""
    import gc
    import json
    import os
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path

    import lancedb
    import pyarrow as pa

    source = Path(source_path).resolve()
    destination = Path(destination_path).resolve()
    if dimension < 1:
        raise ValueError("Embedding dimension must be positive")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Use separate, non-nested source and destination directories")
    if not (source / f"{CAREER_TABLE_NAME}.lance").is_dir():
        raise FileNotFoundError("Source career vector table does not exist")
    target_table = destination / f"{CAREER_TABLE_NAME}.lance"
    if target_table.exists():
        raise FileExistsError("Destination table already exists; it will not be overwritten")

    source_db = lancedb.connect(str(source))
    source_table = source_db[CAREER_TABLE_NAME]
    original_schema = source_table.schema
    original_rows = source_table.to_arrow().to_pylist()
    expected = career_schema(dimension)
    # Preserve any extra business columns in addition to the common schema.
    extra_fields = [field.with_nullable(True) for field in original_schema if field.name not in expected.names]
    outgoing_schema = pa.schema([*expected, *extra_fields], metadata=original_schema.metadata)
    migrated_rows = []
    pending = 0
    for original in original_rows:
        row = dict(original)
        for name in expected.names:
            if name != "embedding":
                row.setdefault(name, "")
        vector = row.get("embedding")
        # Incompatible or old zero placeholders require real recomputation.
        if vector is not None and len(vector) == dimension and any(float(value) != 0 for value in vector):
            row["embedding"] = validate_embedding(vector, dimension)
        else:
            row["embedding"] = None
            pending += 1
        migrated_rows.append(row)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vector-migration-", dir=destination.parent) as staging:
        staging_db_path = Path(staging) / "store"
        staging_db = lancedb.connect(str(staging_db_path))
        data = pa.Table.from_pylist(migrated_rows, schema=outgoing_schema)
        if migrated_rows:
            staged_table = staging_db.create_table(CAREER_TABLE_NAME, data=data)
        else:
            staged_table = staging_db.create_table(CAREER_TABLE_NAME, schema=outgoing_schema)
        open_career_table(staging_db, dimension)
        verified = staged_table.to_arrow().to_pylist()
        if len(verified) != len(original_rows):
            raise RuntimeError("Migrated row count does not match the source")
        for before, after in zip(original_rows, verified):
            if any(after.get(name) != value for name, value in before.items() if name != "embedding"):
                raise RuntimeError("Migration would change business data")
        # Release native dataset handles before moving directories on Windows.
        del staged_table, staging_db, data
        gc.collect()
        destination.mkdir(parents=True, exist_ok=True)
        if target_table.exists():
            raise FileExistsError("Destination table appeared during migration; aborting")
        os.rename(staging_db_path / f"{CAREER_TABLE_NAME}.lance", target_table)

    old_dimension = None
    if "embedding" in original_schema.names:
        old_type = original_schema.field("embedding").type
        if pa.types.is_fixed_size_list(old_type):
            old_dimension = old_type.list_size
    report = {
        "source": str(source), "destination": str(destination),
        "old_dimension": old_dimension, "new_dimension": dimension,
        "rows": len(original_rows), "embeddings_pending": pending,
        "source_unchanged": True, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (destination / "migration_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
