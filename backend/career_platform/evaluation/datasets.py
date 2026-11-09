"""版本化评估集与语料快照的只读加载。

数据集是仓库内的 JSON 文件，按文件内容哈希标识版本，加载后返回深拷贝，
调用方无法修改冻结内容。新增版本只需放入 `datasets/` 目录并在 `version`
字段登记，不修改共享的组装或契约文件。
"""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

DATASET_DIR = Path(__file__).with_name('datasets')
CORPUS_FILE = DATASET_DIR / 'java-corpus-v1.json'
REQUIRED_QUERY_FIELDS = ('id', 'query', 'relevant_ids')


class UnknownDataset(ValueError):
    """数据集版本未登记或文件损坏，调用方应返回 400 而不是空结果。"""


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise UnknownDataset(f'数据集 {path.name} 无法读取') from error
    if not isinstance(payload, dict):
        raise UnknownDataset(f'数据集 {path.name} 格式无效')
    return payload


def fingerprint(payload: dict) -> str:
    """按规范化 JSON 计算指纹，用于在验收记录中说明实际使用的数据版本。"""
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class FrozenDatasetLoader:
    def __init__(self, directory: Path | str = DATASET_DIR):
        self.directory = Path(directory)

    def versions(self) -> dict[str, Path]:
        """扫描目录并按 version 字段登记；同版本重复登记视为配置错误。"""
        registry: dict[str, Path] = {}
        for path in sorted(self.directory.glob('*.json')):
            payload = _read_json(path)
            version = str(payload.get('version', '')).strip()
            if not version or 'queries' not in payload:
                continue
            if version in registry:
                raise UnknownDataset(f'数据集版本 {version} 重复登记')
            registry[version] = path
        return registry

    def load(self, version: str) -> dict:
        path = self.versions().get(str(version))
        if path is None:
            raise UnknownDataset(f'未登记的评估集版本：{version}')
        payload = _read_json(path)
        self._validate(payload, version)
        dataset = deepcopy(payload)
        dataset['sha256'] = fingerprint(payload)
        return dataset

    @staticmethod
    def _validate(payload: dict, version: str) -> None:
        queries = payload.get('queries')
        if not isinstance(queries, list) or not queries:
            raise UnknownDataset(f'评估集 {version} 必须包含非空 queries')
        seen: set[str] = set()
        for index, sample in enumerate(queries, start=1):
            if not isinstance(sample, dict):
                raise UnknownDataset(f'评估集 {version} 第 {index} 条不是对象')
            missing = [field for field in REQUIRED_QUERY_FIELDS if sample.get(field) in (None, '')]
            if missing:
                raise UnknownDataset(f'评估集 {version} 第 {index} 条缺少 {",".join(missing)}')
            if not isinstance(sample['relevant_ids'], list):
                raise UnknownDataset(f'评估集 {version} 第 {index} 条 relevant_ids 必须是数组')
            key = str(sample['id'])
            if key in seen:
                raise UnknownDataset(f'评估集 {version} 的 query id 重复：{key}')
            seen.add(key)


def load_corpus(path: Path | str = CORPUS_FILE) -> tuple[dict, dict]:
    """返回（语料快照，含摘要）。语料只作为排序候选，不写入数据库。"""
    payload = _read_json(Path(path))
    questions = payload.get('questions')
    if not isinstance(questions, list) or not questions:
        raise UnknownDataset(f'语料 {Path(path).name} 必须包含非空 questions')
    return payload, {'version': payload.get('version', ''), 'sha256': fingerprint(payload),
                     'size': len(questions)}
