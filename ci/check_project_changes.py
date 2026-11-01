"""Enforce document ownership and select complete acceptance from Git diff, not flags."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'ci/project_modules.json').read_text(encoding='utf-8'))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def evaluate(changed, bootstrap=False, config=None):
    config = CONFIG if config is None else config
    changed = set(changed)
    modules = {key for key, value in config['modules'].items()
               if any(any(path.startswith(prefix) for prefix in value['paths']) for path in changed)}
    shared = any(any(path.startswith(prefix) for prefix in config['shared_paths']) for path in changed)
    # New backend files outside a known member area cannot escape ownership.
    shared = shared or any(path.startswith('backend/career_platform/') and
        not any(any(path.startswith(prefix) for prefix in value['paths']) for value in config['modules'].values())
        for path in changed)
    needed = {f"docs/implementation/{config['modules'][key]['doc']}" for key in modules}
    if shared:
        needed.add('docs/implementation/00-shared-contracts.md')
        needed.update(f"docs/implementation/{value['doc']}" for value in config['modules'].values())
    # Merely changing a module state/flag never exempts implementation files.
    missing = sorted(needed - changed)
    return {'bootstrap': bootstrap, 'changed_modules': sorted(modules), 'shared_changed': shared,
            'required_documents': sorted(needed), 'missing_documents': missing,
            'complete_tests': [] if bootstrap else sorted(config['modules'] if shared else modules),
            'integration_test': shared and not bootstrap}


def validate_record(content, previous='', bootstrap=False):
    """Changing whitespace alone is not an updated acceptance record."""
    blocks=re.findall(r'```acceptance-record\s*\n(.*?)\n```',content,re.S)
    previous_blocks=re.findall(r'```acceptance-record\s*\n(.*?)\n```',previous,re.S)
    if not blocks:
        return '缺少 acceptance-record 结构化验收记录'
    try:
        record=json.loads(blocks[-1])
    except (ValueError,TypeError):
        return '验收记录不是有效 JSON'
    for field in ('commit','command','result','environment','scope','limitations','evidence'):
        value=record.get(field)
        if not isinstance(value,str) or not value.strip() or any(word in value for word in ('待填写','待执行','TODO')):
            return f'验收记录缺少有效字段: {field}'
    if not re.fullmatch(r'[0-9a-f]{7,40}(?: \+ dirty)?',record['commit']):
        return 'commit 必须包含实际提交号，可追加 + dirty'
    if previous_blocks and json.loads(previous_blocks[-1])==record:
        return '验收记录未更新，不能仅修改空白或正文'
    if not bootstrap and record['result'] not in ('passed','failed'):
        return '后续实施必须记录实际验收结果 passed/failed，不能退回骨架阶段'
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    changed = git('diff', '--name-only', '--diff-filter=ACDMRT', args.base, args.head).splitlines()
    exists = subprocess.run(['git','cat-file','-e',f'{args.base}:ci/project_modules.json'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0
    # Trust the base ownership map once installed. A PR cannot exempt itself by
    # deleting a path or downgrading an implementation flag in its own config.
    config=json.loads(git('show',f'{args.base}:ci/project_modules.json')) if exists else CONFIG
    report = evaluate(changed, bootstrap=not exists,config=config)
    errors={}
    for path in report['required_documents']:
        if path in report['missing_documents']:
            continue
        try:
            content=git('show',f'{args.head}:{path}')
        except subprocess.CalledProcessError:
            errors[path]='要求的文档已被删除'
            continue
        previous_result=subprocess.run(['git','show',f'{args.base}:{path}'],cwd=ROOT,text=True,encoding='utf-8',capture_output=True)
        error=validate_record(content,previous_result.stdout if previous_result.returncode==0 else '',bootstrap=not exists)
        if error: errors[path]=error
    report['document_errors']=errors
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return 1 if report['missing_documents'] or errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
