"""One entrypoint; scaffold success explicitly does not mean business completion."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('catalog','evaluation','resume','rag','records')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['scaffold','complete'], default='scaffold')
    parser.add_argument('--module', choices=['all',*MODULES], default='all')
    parser.add_argument('--output', default=str(ROOT/'output/project-acceptance.json'))
    args = parser.parse_args()
    selected = MODULES if args.module == 'all' else (args.module,)
    labels = ['career_platform.tests.test_scaffold'] if args.stage == 'scaffold' else [f'career_platform.tests.accept_{m}' for m in selected]
    if args.stage == 'complete' and args.module == 'all': labels.append('career_platform.tests.accept_integration')
    command = [sys.executable,'-m','django','test',*labels,'--settings=career_platform.test_settings','--testrunner=career_platform.tests.runner.FixedAcceptanceRunner','--verbosity=1']
    result = subprocess.run(command,cwd=ROOT/'backend')
    dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,text=True).strip())
    report={'stage':args.stage,'modules':list(selected),'passed':result.returncode==0,
            'business_complete':args.stage=='complete' and args.module=='all' and result.returncode==0,
            'business_state':'not_implemented' if args.stage=='scaffold' else ('accepted' if result.returncode==0 else 'failed'),
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'dirty':dirty,
            'environment':'mysql-isolated' if os.getenv('PLATFORM_TEST_MYSQL')=='1' else 'sqlite-isolated',
            'real_model':False}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return result.returncode


if __name__=='__main__': raise SystemExit(main())
