"""Run isolated tests with the same import roots in parent and stdio children."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--scope',choices=['full','new','historical'],default='full');args=p.parse_args()
    if not (ROOT/'AUTHORIZATION.json').is_file():raise SystemExit('Missing development authorization record')
    temp=ROOT/'.test-tmp'
    if temp.is_symlink():raise SystemExit('Refusing symlink test directory')
    temp.mkdir(mode=0o700,exist_ok=True)
    artifact=ROOT/'artifacts'
    if artifact.is_symlink():raise SystemExit('Refusing symlink artifact directory')
    artifact.mkdir(mode=0o700,exist_ok=True)
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(map(str,[ROOT/'src',ROOT/'frozen_payload/source/src']));env['PYTHONDONTWRITEBYTECODE']='1'
    env.pop('AARS_OMB_DB',None)
    targets={'full':['tests','frozen_payload/source/tests'],'new':['tests'],'historical':['frozen_payload/source/tests']}[args.scope]
    command=[sys.executable,'-m','pytest',*targets,'-q','--tb=short','--basetemp='+str(temp/args.scope),'--junitxml='+str(artifact/(args.scope+'.xml'))]
    return subprocess.call(command,cwd=ROOT,env=env)
if __name__=='__main__':raise SystemExit(main())
