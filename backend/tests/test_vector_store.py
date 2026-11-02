"""Exercise real LanceDB files in temporary directories; never touch project data."""

import ast
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import lancedb
import pyarrow as pa
from cs_career_guide.vector_store import (
    CAREER_TABLE_NAME, career_record, career_schema, migrate_career_store,
    open_career_table, validate_embedding, validate_model_dimension,
)


def row(record_id="record-1", embedding=None):
    return {
        "id": record_id, "user_id": "test-user", "self_introduction": "测试文字",
        "introduction_preview": "测试", "recommendations": json.dumps([{"name": "岗位"}], ensure_ascii=False),
        "analysis_result": "测试分析", "created_at": "2026-10-15T00:00:00Z",
        "embedding": embedding,
    }


class VectorStoreTests(unittest.TestCase):
    def test_schema_supports_missing_embeddings_and_real_512_vectors(self):
        with tempfile.TemporaryDirectory() as directory:
            db = lancedb.connect(directory)
            table = open_career_table(db, 512)
            table.add([row(), row("record-2", [0.25] * 512)])
            result = table.to_arrow().to_pylist()
            self.assertEqual(table.schema.field("embedding").type.list_size, 512)
            self.assertIsNone(result[0]["embedding"])
            self.assertEqual(len(result[1]["embedding"]), 512)

    def test_wrong_dimensions_fail_instead_of_padding_or_truncating(self):
        with self.assertRaisesRegex(ValueError, "384 dimensions; expected 512"):
            validate_embedding([0.1] * 384, 512)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_embedding([float("nan")] * 512, 512)
        model = SimpleNamespace(get_sentence_embedding_dimension=lambda: 384)
        with self.assertRaisesRegex(ValueError, "Model outputs 384"):
            validate_model_dimension(model, 512)

    def test_existing_old_schema_requires_explicit_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            db = lancedb.connect(directory)
            db.create_table(CAREER_TABLE_NAME, schema=career_schema(384))
            with self.assertRaisesRegex(ValueError, "migrate_vector_store.py"):
                open_career_table(db, 512)

    def test_migration_preserves_source_and_all_business_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            db = lancedb.connect(str(source))
            original = [row("record-1", [0.2] * 384), row("record-2", [0.0] * 384)]
            db.create_table(CAREER_TABLE_NAME, data=pa.Table.from_pylist(original, schema=career_schema(384)))
            report = migrate_career_store(source, target, 512)
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["embeddings_pending"], 2)
            unchanged = db[CAREER_TABLE_NAME].to_arrow().to_pylist()
            self.assertEqual(unchanged[0]["embedding"], [float(pa.scalar(0.2, type=pa.float32()).as_py())] * 384)
            migrated = open_career_table(lancedb.connect(str(target)), 512).to_arrow().to_pylist()
            for before, after in zip(unchanged, migrated):
                self.assertIsNone(after["embedding"])
                self.assertEqual({key: value for key, value in before.items() if key != "embedding"},
                                 {key: value for key, value in after.items() if key != "embedding"})

    def test_legacy_six_column_store_gains_common_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            names = [name for name in career_schema(512).names if name not in {"embedding", "introduction_preview"}]
            legacy_schema = pa.schema([(name, pa.string()) for name in names])
            legacy_row = {name: row()[name] for name in names}
            db = lancedb.connect(str(source))
            db.create_table(CAREER_TABLE_NAME, data=pa.Table.from_pylist([legacy_row], schema=legacy_schema))
            migrate_career_store(source, target, 512)
            migrated = open_career_table(lancedb.connect(str(target)), 512).to_arrow().to_pylist()[0]
            self.assertEqual(migrated["introduction_preview"], "")
            self.assertIsNone(migrated["embedding"])

    def test_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            lancedb.connect(str(source)).create_table(CAREER_TABLE_NAME, schema=career_schema(384))
            target_db = lancedb.connect(str(target))
            target_table = open_career_table(target_db, 512)
            target_table.add([row("existing-record")])
            with self.assertRaises(FileExistsError):
                migrate_career_store(source, target, 512)
            self.assertEqual(target_table.count_rows(), 1)

    def test_record_writer_serializes_json_and_checks_dimensions(self):
        data = row()
        data["recommendations"] = [{"name": "岗位"}]
        self.assertEqual(json.loads(career_record(data, 512)["recommendations"]), data["recommendations"])
        data["embedding"] = [0.1] * 384
        with self.assertRaises(ValueError):
            career_record(data, 512)

    def test_sync_upsert_uses_common_schema_and_preserves_other_records(self):
        source = BACKEND_DIR / "ai_integration/arag_integration.py"
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        search_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ARAGCareerSearch")
        method = next(node for node in search_class.body if isinstance(node, ast.FunctionDef) and node.name == "add_record")
        namespace = {
            "Dict": dict, "Any": object, "logger": Mock(),
            "settings": SimpleNamespace(EMBEDDING_DIMENSION=512),
            "career_record": career_record, "validate_embedding": validate_embedding,
            "career_schema": career_schema, "pa": pa,
        }
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
        with tempfile.TemporaryDirectory() as directory:
            table = open_career_table(lancedb.connect(directory), 512)
            table.add([row("other-record")])
            search = SimpleNamespace(table=table, _get_model=lambda: None)
            data = row("synced-record")
            self.assertTrue(namespace["add_record"](search, data, upsert=True), str(namespace["logger"].error.call_args))
            data["analysis_result"] = "更新后的分析"
            self.assertTrue(namespace["add_record"](search, data, upsert=True))
            records = {item["id"]: item for item in table.to_arrow().to_pylist()}
            self.assertEqual(table.count_rows(), 2)
            self.assertIn("other-record", records)
            self.assertEqual(records["synced-record"]["analysis_result"], "更新后的分析")
            self.assertIsNone(records["synced-record"]["embedding"])


class PromptInitializationTests(unittest.TestCase):
    def test_ready_registers_initialization_after_migrations_only(self):
        from django.db.models.signals import post_migrate
        from ai_integration.apps import AiIntegrationConfig

        app = AiIntegrationConfig("ai_integration", importlib.import_module("ai_integration"))
        initialize = Mock()
        try:
            with patch.dict(sys.modules, {
                "ai_integration.langgraph.utils.prompt_manager": SimpleNamespace(initialize_prompts=initialize),
            }):
                app.ready()
                initialize.assert_not_called()
                post_migrate.send(sender=app, using="default")
                initialize.assert_called_once_with()
        finally:
            post_migrate.disconnect(sender=app, dispatch_uid="ai_integration.initialize_prompts")


if __name__ == "__main__":
    unittest.main()
