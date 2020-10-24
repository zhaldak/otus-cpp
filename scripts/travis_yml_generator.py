#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import datetime


def _log(prefix, color, message, color_full_line=True):
    if color_full_line:
        print(f'{color}{prefix}: {message}\033[0m');
    else:
        print(f'{color}{prefix}:\033[0m {message}');

def log_t(msg): _log('TRC', '\033[90m', msg, color_full_line=True)
def log_d(msg): _log('DBG', '\033[39m', msg)
def log_i(msg): _log('INF', '\033[94m', msg)
def log_w(msg): _log('WRN', '\033[33m', msg)
def log_e(msg): _log('ERR', '\033[91m', msg)



def shell_exec(cmd, timeout_s=5, check_succ=True):
    cmd_copy     = []
    quoter_parts = []
    quoter_type  = '"'
    for p in cmd.split():
        if quoter_parts:
            if not p.endswith(quoter_type):
                quoter_parts.append(p)
            else:
                quoter_parts.append(p[:-1])
                cmd_copy.append(' '.join(quoter_parts))
                quoter_parts.clear()
        else:
            if p.startswith('"'):
                quoter_type = '"'
                if p.endswith(quoter_type):
                    cmd_copy.append(p)
                else:
                    quoter_parts.append(p[1:])
            elif p.startswith("'"):
                quoter_type = "'"
                if p.endswith(quoter_type):
                    cmd_copy.append(p)
                else:
                    quoter_parts.append(p[1:])
            else:
                cmd_copy.append(p)
    log_t('C>[{}]'.format(' '.join(cmd_copy)))
    res = subprocess.run(cmd_copy, capture_output=True, timeout=timeout_s)
    ec  = res.returncode
    out = res.stdout.decode('utf-8').rstrip()
    if out and len(out.split('\n')) > 1:
        log_t(f'R({ec})<\n{out}')
    else:
        log_t(f'R({ec})<[{out}]')
    if check_succ:
        res.check_returncode()
        return out
    return ec, out



class Config:
    CTRL_PREFIXES           = ['hw']
    GIT_ROOT                = '.'
    GIT_INIT_COMMIT         = 'd829c61855aff7241e12d8578d4a66a7118eb327'
    TRAVIS_CI_DIR           = '.git/travis-ci'
    LAST_GREEN_COMMIT_FNAME = '.git/travis-ci/last_green_build_commit'
    STATE_FNAME             = '.git/travis-ci/state'
    NEED_INIT               = False
    SET_READY               = False
    SAVE_COMMIT             = None
    IS_CONTINUE             = False

    @staticmethod
    def init_cfg():
        log_d('class @Config initialisation')
        Config.GIT_INIT_COMMIT         = shell_exec('git rev-list --max-parents=0 HEAD')
        Config.GIT_ROOT                = shell_exec('git rev-parse --show-toplevel').strip()
        Config.TRAVIS_CI_DIR           = f'{Config.GIT_ROOT}/.git/travis-ci'
        Config.LAST_GREEN_COMMIT_FNAME = f'{Config.TRAVIS_CI_DIR}/last_green_build_commit'
        Config.STATE_FNAME             = f'{Config.TRAVIS_CI_DIR}/state'

    @staticmethod
    def self_path(is_abs=False):
        rel_path = 'scripts/travis_yml_generator.py'
        return f'{Config.GIT_ROOT}/{rel_path}' if is_abs else rel_path

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(
            description='Generator of Tracis-CI configuration before pushing changes to GitHub')
        parser.add_argument('--init',       action='store_true', help='Initialize repo for developer')
        parser.add_argument('--set_ready',  action='store_true', help='Approve pushing changes')
        parser.add_argument('--set_commit', metavar='HASH',      help='Set last \033[92mGREEN\033[0m commit')
        parser.add_argument('--exec_main',   action='store_true', help='Execute main functionality')
        args = parser.parse_args()
        Config.NEED_INIT   = args.init
        Config.SET_READY   = args.set_ready
        Config.SAVE_COMMIT = args.set_commit
        Config.IS_CONTINUE = args.exec_main

    @staticmethod
    def set_state(state):
        assert type(state) == type(True)
        with open(Config.STATE_FNAME, 'w') as f:
            f.write('READY' if state else 'NOT READY')

    @staticmethod
    def get_state():
        if not os.path.isfile(Config.STATE_FNAME): return False
        state = ''
        with open(Config.STATE_FNAME, 'r') as f: state = f.readline().strip()
        if not state: return False
        return state == 'READY'

    @staticmethod
    def create_working_dir_if_needed():
        if not os.path.isdir(Config.TRAVIS_CI_DIR):
            os.mkdir(Config.TRAVIS_CI_DIR, mode=0o755)

    @staticmethod
    def set_commit(commit):
        with open(Config.LAST_GREEN_COMMIT_FNAME, 'w') as f:
            f.write(commit)

def gen_warning():
    return """# This is autogen file by tools/travis_yml_generator.py
# Do not change it manualy because after a next `git push` command this file
#   will be regenerated.
#

"""


def last_green_travis_build():
    commit = ''
    if os.path.isfile(Config.LAST_GREEN_COMMIT_FNAME):
        with open(Config.LAST_GREEN_COMMIT_FNAME, 'r') as f: commit = f.readline()
    return commit if commit else Config.GIT_INIT_COMMIT


def gen_travis_yaml(changed):
    TRAVIS_YAML_NAME = f'{Config.GIT_ROOT}/.travis.yml'

    if not changed: return False
    stage_parts = []
    for changed_dir in changed:
        yml_part = '    - script: '
        if not stage_parts:
            yml_part = '    - stage: Build && Test && Package\n      script: '
        commands = [
            f"echo '{changed_dir}'",
            f"pushd '{changed_dir}'",
            "mkdir build",
            "cd build",
            "cmake ..",
            "cmake --build .",
            "cmake --build . --target test",
            "cmake --build . --target package",
            "popd",
        ]
        yml_part += ' && '.join(commands)
        stage_parts.append(yml_part)

    with open(TRAVIS_YAML_NAME, 'w') as f:
        f.write(gen_warning())
        f.write("""language: cpp

before_script:
- sudo apt-get install libboost-test-dev -y
- echo "deb http://archive.ubuntu.com/ubuntu xenial main universe" | sudo tee -a /etc/apt/sources.list
- sudo apt-get update -qq

jobs:
  include:
""")
        for part in stage_parts: f.write(part)
#        f.write("""
#deploy:
#  provider: script
#  skip_cleanup: true
#  script:
#  - curl -T helloworld-0.0.$TRAVIS_BUILD_NUMBER-Linux.deb -ustarokurov:$BINTRAY_API_KEY "https://api.bintray.com/content/starokurov/otus-cpp/helloworld/$TRAVIS_BUILD_NUMBER/helloworld-0.0.$TRAVIS_BUILD_NUMBER-Linux.deb;deb_distribution=trusty;deb_component=main;deb_architecture=amd64;publish=1"
#""")
    return TRAVIS_YAML_NAME


def commit_changes(yml):
    shell_exec(f'git add {yml}')
    if [1 for line in shell_exec('git status -s').split('\n') if not line.startswith('??')]:
        shell_exec(f'git commit -m "[AUTO] regen {yml} before pushing"')


def InitRepo():
    Config.create_working_dir_if_needed()
    Config.set_commit(Config.GIT_INIT_COMMIT)
    Config.set_state(False)
    with open(f'{Config.GIT_ROOT}/.git/hooks/pre-push', 'w') as f:
        f.write('''#!/bin/sh

#
# This file was generated by scripts/travis_yml_generator.py
# Creation time point: {1}
#

if [ -f '{0}' ] ; then
    python3 '{0}'
else
    echo "ERROR: can't find ['{0}']"
    exit 1
fi
'''.format(Config.self_path(), datetime.datetime.now().isoformat()))





def main():
    Config.parse_args()
    Config.init_cfg()
    need_exit = False
    if Config.NEED_INIT:   InitRepo(); need_exit = True
    if Config.SET_READY:   Config.set_state(True); need_exit = True
    if Config.SAVE_COMMIT: Config.set_commit(Config.SAVE_COMMIT); need_exit = True
    if Config.IS_CONTINUE: need_exit = False
    if need_exit: return

    log_i('Getting last green commit')
    last_green = last_green_travis_build()
    if not Config.get_state():
        log_e('''
=======================================
!!! 'git push' command was disabled !!!
=======================================

Latest saved commit: {0}

Set a new commit:      --set_commit NEW_COMMIT
Enabling 'git push':   --set_ready

Possible commads:
{1} --set_ready
{1} --set_commit NEW_COMMIT
{1} --set_ready --set_commit NEW_COMMIT

'''.format(last_green, Config.self_path(is_abs=True)))
        return 1

    log_i('Collect valued changes')
    changed = set()
    for line in shell_exec(f'git diff --name-only HEAD {last_green}').split('\n'):
        file_root = line.split('/')[0]
        for prefix in Config.CTRL_PREFIXES:
            if file_root.startswith(prefix):
                changed.add(file_root)
                break
    if changed:
        log_i('Generation CI configuration')
        yml_name = gen_travis_yaml(changed)
        commit_changes(yml_name)
    log_w('Disable "git push"')
    Config.set_state(False)
    return 0


if __name__ == '__main__':
    sys.exit(main())

