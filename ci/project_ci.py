"""Run selected acceptance from the document gate report, never a stage flag."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--selection',required=True)
    args=parser.parse_args()
    report=json.loads(Path(args.selection).read_text(encoding='utf-8'))
    if report['missing_documents'] or report.get('document_errors'):
        raise SystemExit('Document gate must pass before acceptance')
    suffix='mysql' if os.getenv('PLATFORM_TEST_MYSQL')=='1' else 'sqlite'
    def run(stage,module='all'):
        return subprocess.run([sys.executable,str(ROOT/'ci/project_acceptance.py'),'--stage',stage,'--module',module,
            '--output',str(ROOT/f'output/acceptance-{suffix}-{stage}-{module}.json')],cwd=ROOT).returncode
    if run('scaffold'):
        return 1
    if report['bootstrap']:
        # Prove unfinished services cannot pass a complete suite. This check is
        # specific to the initial scaffold and disappears once its base contains
        # the ownership map. A test import/config failure is not acceptable proof.
        for module in ('catalog','evaluation','resume','rag','records'):
            command=[sys.executable,str(ROOT/'ci/project_acceptance.py'),'--stage','complete','--module',module,
                '--output',str(ROOT/f'output/expected-rejection-{suffix}-{module}.json')]
            process=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            log=process.stdout+process.stderr
            (ROOT/f'output/expected-rejection-{suffix}-{module}.log').write_text(log,encoding='utf-8')
            if process.returncode==0 or ('501' not in log and 'FeatureNotImplemented' not in log) or 'ImportError' in log or 'ModuleNotFoundError' in log:
                print(f'{module}: expected a real not-implemented acceptance failure',file=sys.stderr)
                return 1
            print(f'{module}: complete acceptance correctly rejected unfinished business')
        return 0
    if report.get('integration_test'):
        return run('complete')
    return int(any(run('complete',module) for module in report['complete_tests']))


if __name__=='__main__': raise SystemExit(main())
