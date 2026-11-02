"""Configuration regression tests that do not connect to databases or AI services."""

import ast
import logging
import os
import runpy
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from django.core.exceptions import ImproperlyConfigured
from cs_career_guide.env import env_bool, env_int
from cs_career_guide.ai_config import get_llm_kwargs
from cs_career_guide.vector_store import validate_model_dimension


class EnvironmentConfigTests(unittest.TestCase):
    required = {
        "SECRET_KEY": "test-signing-key-only",
        "DATABASE_NAME": "test_db",
        "DATABASE_USER": "test_user",
        "DATABASE_PASSWORD": "test-password-only",
    }

    def load_settings(self, **overrides):
        with patch.dict(os.environ, {**self.required, **overrides}, clear=True):
            with patch("dotenv.load_dotenv"):
                return runpy.run_module("cs_career_guide.settings")

    def test_database_and_host_overrides(self):
        config = self.load_settings(
            DATABASE_HOST="db.internal", DATABASE_PORT="3307",
            DATABASE_CONN_MAX_AGE="45", ALLOWED_HOSTS=" site.test, api.site.test, ",
        )
        database = config["DATABASES"]["default"]
        self.assertEqual(database["HOST"], "db.internal")
        self.assertEqual(database["PORT"], 3307)
        self.assertEqual(database["NAME"], "test_db")
        self.assertEqual(database["USER"], "test_user")
        self.assertEqual(database["PASSWORD"], "test-password-only")
        self.assertEqual(database["CONN_MAX_AGE"], 45)
        self.assertEqual(config["ALLOWED_HOSTS"], ["site.test", "api.site.test"])

    def test_required_configuration_has_no_password_fallback(self):
        for missing in self.required:
            values = {key: value for key, value in self.required.items() if key != missing}
            with self.subTest(missing=missing), patch.dict(os.environ, values, clear=True):
                with patch("dotenv.load_dotenv"):
                    with self.assertRaisesRegex(ImproperlyConfigured, missing):
                        runpy.run_module("cs_career_guide.settings")

    def test_boolean_defaults_and_cors(self):
        defaults = self.load_settings()
        self.assertFalse(defaults["DEBUG"])
        self.assertFalse(defaults["CORS_ALLOW_ALL_ORIGINS"])
        self.assertFalse(defaults["ENABLE_TTS"])
        config = self.load_settings(
            DEBUG="true", CORS_ALLOW_ALL_ORIGINS="YES", ENABLE_TTS="1",
            CORS_ALLOWED_ORIGINS="https://ui.test, https://other.test",
            CSRF_TRUSTED_ORIGINS="https://ui.test",
        )
        self.assertTrue(config["DEBUG"])
        self.assertTrue(config["ENABLE_TTS"])
        self.assertEqual(config["CORS_ALLOWED_ORIGINS"], ["https://ui.test", "https://other.test"])
        self.assertEqual(config["CSRF_TRUSTED_ORIGINS"], ["https://ui.test"])

    def test_legacy_aliases_and_speech_key_fallback(self):
        config = self.load_settings(
            api_key="legacy-test-key", base_url="https://legacy.test/v1",
            career_report_model="legacy-report", WSS_URL="wss://speech.test/ws",
            LLM_MODEL="chat-model",
        )
        self.assertEqual(config["LLM_API_KEY"], "legacy-test-key")
        self.assertEqual(config["LLM_BASE_URL"], "https://legacy.test/v1")
        self.assertEqual(config["CAREER_REPORT_MODEL"], "legacy-report")
        self.assertEqual(config["ASR_API_KEY"], "legacy-test-key")
        self.assertEqual(config["ASR_WSS_URL"], "wss://speech.test/ws")
        self.assertEqual(config["TTS_WSS_URL"], "wss://speech.test/ws")

    def test_canonical_variables_override_legacy_names(self):
        config = self.load_settings(
            api_key="legacy", LLM_API_KEY="canonical",
            base_url="https://legacy.test", LLM_BASE_URL="https://canonical.test",
            LLM_MODEL="configured-model", ASR_API_KEY="asr-key", TTS_API_KEY="tts-key",
            WSS_URL="wss://legacy.test", ASR_WSS_URL="wss://asr.test", TTS_WSS_URL="wss://tts.test",
        )
        self.assertEqual(config["LLM_API_KEY"], "canonical")
        self.assertEqual(config["LLM_BASE_URL"], "https://canonical.test")
        self.assertEqual(config["CAREER_REPORT_MODEL"], "configured-model")
        self.assertEqual(config["ASR_API_KEY"], "asr-key")
        self.assertEqual(config["TTS_API_KEY"], "tts-key")
        self.assertEqual(config["ASR_WSS_URL"], "wss://asr.test")
        self.assertEqual(config["TTS_WSS_URL"], "wss://tts.test")

    def test_relative_paths_are_based_on_backend_directory(self):
        config = self.load_settings(
            LANCEDB_PATH="data/vectors", STATIC_ROOT="data/static", MEDIA_ROOT="data/uploads",
            SEARCH_MAX_WORKERS="1",
        )
        self.assertEqual(config["LANCEDB_PATH"], BACKEND_DIR / "data/vectors")
        self.assertEqual(config["STATIC_ROOT"], BACKEND_DIR / "data/static")
        self.assertEqual(config["MEDIA_ROOT"], BACKEND_DIR / "data/uploads")
        self.assertEqual(config["SEARCH_MAX_WORKERS"], 1)

    def test_invalid_boolean_and_numeric_values_fail_clearly(self):
        with patch.dict(os.environ, {"TEST_BOOL": "maybe", "TEST_INT": "wrong"}, clear=True):
            with self.assertRaisesRegex(ImproperlyConfigured, "TEST_BOOL"):
                env_bool("TEST_BOOL")
            with self.assertRaisesRegex(ImproperlyConfigured, "TEST_INT"):
                env_int("TEST_INT", 1)
        for port in ("0", "65536"):
            with self.subTest(port=port), self.assertRaisesRegex(ImproperlyConfigured, "DATABASE_PORT"):
                self.load_settings(DATABASE_PORT=port)
        with self.assertRaisesRegex(ImproperlyConfigured, "SEARCH_MAX_WORKERS"):
            self.load_settings(SEARCH_MAX_WORKERS="0")

    def test_shared_llm_options_and_report_model(self):
        config = SimpleNamespace(
            LLM_API_KEY="test-key", LLM_BASE_URL="https://model.test/v1",
            LLM_MODEL="chat-test", CAREER_REPORT_MODEL="report-test", LLM_TIMEOUT=37,
        )
        with patch("cs_career_guide.ai_config.settings", config):
            self.assertEqual(get_llm_kwargs()["model"], "chat-test")
            self.assertEqual(get_llm_kwargs("CAREER_REPORT_MODEL")["model"], "report-test")
            self.assertEqual(get_llm_kwargs()["timeout"], 37)
            config.LLM_MODEL = ""
            with self.assertRaisesRegex(ImproperlyConfigured, "LLM_MODEL"):
                get_llm_kwargs()

    def test_process_environment_wins_over_dotenv_file(self):
        from dotenv import load_dotenv

        with tempfile.TemporaryDirectory() as directory:
            dotenv_file = Path(directory) / ".env"
            dotenv_file.write_text("DATABASE_HOST=from-file.test\nDATABASE_PORT=3308\n", encoding="utf-8")
            with patch.dict(os.environ, {**self.required, "DATABASE_HOST": "from-process.test"}, clear=True):
                with patch("dotenv.load_dotenv", side_effect=lambda **kwargs: load_dotenv(dotenv_file)):
                    config = runpy.run_module("cs_career_guide.settings")
            self.assertEqual(config["DATABASES"]["default"]["HOST"], "from-process.test")
            self.assertEqual(config["DATABASES"]["default"]["PORT"], 3308)

    def test_example_configuration_loads_after_required_secrets_are_filled(self):
        from dotenv import dotenv_values

        example = dotenv_values(BACKEND_DIR / ".env.example")
        config = self.load_settings(**{**example, **self.required})
        self.assertEqual(config["LLM_MODEL"], "qwen-turbo-2025-07-15")
        self.assertEqual(config["SEARCH_MAX_WORKERS"], 1)
        self.assertEqual(config["CAREER_REPORT_MAX_WORKERS"], 1)
        self.assertFalse(config["EMBEDDING_ALLOW_DOWNLOAD"])


class DatabaseConnectionTests(unittest.TestCase):
    def test_search_pool_keeps_special_characters_in_database_credentials(self):
        from sqlalchemy import URL

        source = BACKEND_DIR / "ai_integration/langgraph/tools/keyword_search.py"
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        method = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_connection_pool")
        engine_factory = Mock(return_value=object())
        password = "test@password:/?#%"
        namespace = {
            "_connection_pool": None, "_pool_lock": threading.Lock(),
            "SQLALCHEMY_AVAILABLE": True, "URL": URL,
            "_db_user": "user@test", "_db_password": password,
            "_db_host": "db.internal", "_db_port": 3307,
            "_db_name": "test_db", "_db_charset": "utf8mb4",
            "QueuePool": object, "create_engine": engine_factory,
            "POOL_CONFIG": {"max_connections": 2, "min_connections": 1, "pool_timeout": 5, "recycle": 60},
            "logger": Mock(spec=logging.Logger),
        }
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
        self.assertIs(namespace["get_connection_pool"](), engine_factory.return_value)
        connection_url = engine_factory.call_args.args[0]
        self.assertEqual(connection_url.username, "user@test")
        self.assertEqual(connection_url.password, password)
        self.assertEqual(connection_url.host, "db.internal")
        self.assertEqual(engine_factory.call_args.kwargs["pool_size"], 1)


class EmbeddingConfigurationTests(unittest.TestCase):
    def invoke_loader(self, config, factory):
        # Execute the real loader in isolation so tests need neither PyTorch nor LanceDB.
        source = BACKEND_DIR / "ai_integration/arag_integration.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        search_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ARAGCareerSearch")
        method = next(node for node in search_class.body if isinstance(node, ast.FunctionDef) and node.name == "_get_model")
        namespace = {"os": os, "settings": config, "logger": Mock(spec=logging.Logger)}
        namespace["validate_model_dimension"] = validate_model_dimension
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
        instance = SimpleNamespace(_model=None, _model_lock=threading.Lock())
        with patch.dict(sys.modules, {"sentence_transformers": SimpleNamespace(SentenceTransformer=factory)}):
            return namespace["_get_model"](instance)

    def configuration(self, **overrides):
        return SimpleNamespace(**{
            "BASE_DIR": BACKEND_DIR, "EMBEDDING_MODEL": "test/model",
            "EMBEDDING_MODEL_PATH": "", "EMBEDDING_DEVICE": "cpu",
            "EMBEDDING_ALLOW_DOWNLOAD": False, **overrides,
            "EMBEDDING_ENABLED": overrides.get("EMBEDDING_ENABLED", True),
            "EMBEDDING_DIMENSION": overrides.get("EMBEDDING_DIMENSION", 512),
        })

    def test_explicit_local_path_is_loaded_without_network(self):
        factory = Mock(return_value=SimpleNamespace(get_sentence_embedding_dimension=lambda: 512))
        with tempfile.TemporaryDirectory() as directory:
            config = self.configuration(EMBEDDING_MODEL_PATH=directory)
            self.assertIs(self.invoke_loader(config, factory), factory.return_value)
            factory.assert_called_once_with(directory, device="cpu", local_files_only=True)

    def test_offline_hub_cache_lookup_cannot_download(self):
        factory = Mock(return_value=SimpleNamespace(get_sentence_embedding_dimension=lambda: 512))
        config = self.configuration()
        with patch("os.path.exists", return_value=False):
            self.invoke_loader(config, factory)
        factory.assert_called_once_with("test/model", device="cpu", local_files_only=True)

    def test_download_flag_is_passed_to_model_loader(self):
        factory = Mock(return_value=SimpleNamespace(get_sentence_embedding_dimension=lambda: 512))
        config = self.configuration(EMBEDDING_ALLOW_DOWNLOAD=True, EMBEDDING_DEVICE="cuda")
        with patch("os.path.exists", return_value=False):
            self.invoke_loader(config, factory)
        factory.assert_called_once_with("test/model", device="cuda", local_files_only=False)

    def test_disabled_embeddings_do_not_load_a_model(self):
        factory = Mock(side_effect=AssertionError("Model must not be loaded"))
        config = self.configuration(EMBEDDING_ENABLED=False)
        self.assertIsNone(self.invoke_loader(config, factory))
        factory.assert_not_called()

    def test_wrong_model_dimension_is_not_cached(self):
        factory = Mock(return_value=SimpleNamespace(get_sentence_embedding_dimension=lambda: 384))
        with tempfile.TemporaryDirectory() as directory:
            config = self.configuration(EMBEDDING_MODEL_PATH=directory)
            self.assertIsNone(self.invoke_loader(config, factory))


if __name__ == "__main__":
    unittest.main()
