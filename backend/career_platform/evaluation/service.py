"""成员2：评估运行、指标聚合与结果导出。

一个成功响应必须能复现：数据集版本与指纹、策略、参数、逐例预测与指标一起
写进 EvaluationRun；列表、详情与导出都只读同一条记录，不会在导出时重新调用
策略或模型。
"""
from django.db import IntegrityError, transaction
from rest_framework.exceptions import APIException, NotFound, ValidationError

from ..composition_base import UnavailableService
from ..models import EvaluationRun
from .datasets import FrozenDatasetLoader, UnknownDataset
from .metrics import METRIC_KEYS, aggregate_metrics, ranking_metrics, unique_ids
from .strategies import build_default_strategies

DEFAULT_TOP_K = 5
MAX_TOP_K = 20
PARAMETER_WHITELIST = ('k',)
# 审计字段随参数一起落库，便于复现；它们由服务端计算，不属于用户白名单参数。
EVALUATION_CONTRACT = 'metrics-v1'
MODEL_VERSION = 'offline-text-v1'


class EvaluationConflict(APIException):
    status_code = 409
    default_detail = '相同 request_id 已用于不同的评估输入，请换一个 request_id'
    default_code = 'CONFLICT'


class EvaluationDependencyUnavailable(APIException):
    status_code = 503
    default_detail = '评估策略不可用，未产生有效基线'

    default_code = 'MODEL_UNAVAILABLE'


class EvaluationService(UnavailableService):
    def __init__(self, *, strategies=None, dataset_loader=None):
        super().__init__('evaluation')
        self._strategies = strategies
        self._built = None
        self.dataset_loader = dataset_loader if dataset_loader is not None else FrozenDatasetLoader()

    # -- 公开操作 ---------------------------------------------------------
    def run(self, *, user, data):
        task = data['task']
        version = data['dataset_version']
        name = data['strategy']
        request_id = data['request_id']
        parameters = self._validated_parameters(data.get('parameters') or {})

        existing = EvaluationRun.objects.filter(user=user, request_id=request_id).first()
        if existing is not None:
            return self._replay(existing, task, version, name, parameters['k'])

        dataset = self._load_dataset(version)
        expected_task = dataset.get('task')
        if expected_task and expected_task != task:
            raise ValidationError({'task': f'评估集 {version} 属于 {expected_task} 任务'})
        strategy, _corpus = self._strategy(name)

        results, failures = self._execute(strategy, dataset, parameters['k'])
        if failures and not [item for item in results if item['metrics'] is not None]:
            raise EvaluationDependencyUnavailable(
                f'全部 {failures} 个样本执行失败，没有产生有效指标')
        relevant = [item['metrics'] for item in results
                    if item['metrics'] is not None and item['group'] == 'relevant']
        run = self._create(user, request_id, task, version, name, parameters, dataset,
                           aggregate_metrics(relevant), results)
        return self.describe(run)

    def list_runs(self, *, user, data):
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 20))
        queryset = EvaluationRun.objects.filter(user=user).order_by('created_at', 'id')
        offset = (page - 1) * page_size
        runs = list(queryset[offset:offset + page_size])
        return {'count': queryset.count(), 'page': page, 'page_size': page_size,
                'results': [self._summary(run) for run in runs]}

    def get_run(self, *, user, data):
        return self.describe(self._owned_run(user, data['id']))

    def export(self, *, user, data):
        """导出已保存的结果，不重新执行策略，保证与详情完全一致。"""
        run = self._owned_run(user, data['id'])
        payload = self.describe(run)
        payload['contract_version'] = EVALUATION_CONTRACT
        payload['exported_at'] = run.updated_at.isoformat()
        payload['groups'] = self._groups(run.results)
        return payload

    # -- 内部实现 ---------------------------------------------------------
    def _validated_parameters(self, parameters):
        if not isinstance(parameters, dict):
            raise ValidationError({'parameters': '必须是对象'})
        unknown = sorted(set(parameters) - set(PARAMETER_WHITELIST))
        if unknown:
            raise ValidationError({key: '当前评估任务不接受该参数' for key in unknown})
        k = parameters.get('k', DEFAULT_TOP_K)
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= MAX_TOP_K:
            raise ValidationError({'k': f'必须是 1 到 {MAX_TOP_K} 的整数'})
        return {'k': k}

    def _strategy(self, name):
        strategies, summary = self._strategy_table()
        strategy = strategies.get(str(name))
        if strategy is None:
            raise ValidationError({'strategy': f'未注册的评估策略：{name}',
                                   'available': sorted(strategies)})
        return strategy, summary

    def _strategy_table(self):
        if self._strategies is not None:
            return self._strategies, {}
        if self._built is None:
            self._built = build_default_strategies()
        return self._built

    def _load_dataset(self, version):
        try:
            return self.dataset_loader.load(version)
        except UnknownDataset as error:
            raise ValidationError({'dataset_version': str(error)}) from error
        except ValueError as error:
            raise ValidationError({'dataset_version': f'评估集不可用：{error}'}) from error

    def _execute(self, strategy, dataset, k):
        corpus_ids = dataset.get('corpus_ids')
        corpus_index = {str(item) for item in corpus_ids} if isinstance(corpus_ids, list) else None
        results, failures = [], 0
        for index, sample in enumerate(dataset['queries'], start=1):
            query_id = str(sample.get('id') or f'q{index}')
            relevant = [str(item) for item in sample.get('relevant_ids') or []]
            group = sample.get('group') or ('unrelated' if not relevant else 'relevant')
            record = {'query_id': query_id, 'query': str(sample.get('query', '')),
                      'group': group, 'relevant_ids': relevant,
                      'predicted_ids': [], 'metrics': None, 'failure': None}
            if corpus_index is not None:
                record['unknown_ids'] = []
            try:
                predicted = strategy.rank(query=record['query'], top_k=k)
            except Exception as error:  # 适配器异常只记录类型，避免泄露供应商细节
                failures += 1
                record['failure'] = type(error).__name__
                results.append(record)
                continue
            predicted = unique_ids(predicted)[:k]
            record['predicted_ids'] = predicted
            if corpus_index is not None:
                record['unknown_ids'] = [item for item in predicted if item not in corpus_index]
            record['metrics'] = ranking_metrics(
                relevant_ids=relevant, predicted_ids=predicted, k=k)
            results.append(record)
        return results, failures

    def _create(self, user, request_id, task, version, name, parameters, dataset, metrics, results):
        stored = {'k': parameters['k'], 'evaluation_contract': EVALUATION_CONTRACT}
        if dataset.get('sha256'):
            stored['dataset_sha256'] = dataset['sha256']
        if dataset.get('corpus_version'):
            stored['corpus_version'] = dataset['corpus_version']
        try:
            with transaction.atomic():
                return EvaluationRun.objects.create(
                    user=user, request_id=request_id, status='succeeded', task=task,
                    dataset_version=version, strategy=name, parameters=stored,
                    metrics=metrics, results=results, model_version=MODEL_VERSION)
        except IntegrityError:
            # 并发提交同一个 request_id 时以先落库的记录为准。
            existing = EvaluationRun.objects.get(user=user, request_id=request_id)
            return self._replay(existing, task, version, name, parameters['k'])

    def _replay(self, run, task, version, name, k):
        same_input = (run.task == task and run.dataset_version == version
                      and run.strategy == name and (run.parameters or {}).get('k') == k)
        if not same_input:
            raise EvaluationConflict()
        return self.describe(run)

    def _owned_run(self, user, run_id):
        run = EvaluationRun.objects.filter(pk=run_id, user=user).first()
        if run is None:
            raise NotFound('评估记录不存在')
        return run

    @staticmethod
    def _groups(results):
        groups = {}
        for item in results:
            groups[item.get('group', 'relevant')] = groups.get(item.get('group', 'relevant'), 0) + 1
        return groups

    def _failure_count(self, results):
        return sum(1 for item in results if item.get('failure'))

    def _summary(self, run):
        return {'id': str(run.id), 'task': run.task, 'dataset_version': run.dataset_version,
                'strategy': run.strategy, 'parameters': run.parameters,
                'metrics': run.metrics, 'model_version': run.model_version,
                'status': run.status, 'created_at': run.created_at.isoformat(),
                'sample_count': len(run.results),
                'failure_count': self._failure_count(run.results),
                'groups': self._groups(run.results)}

    def describe(self, run):
        summary = self._summary(run)
        summary['request_id'] = str(run.request_id)
        summary['results'] = run.results
        summary['metric_keys'] = list(METRIC_KEYS)
        return summary
