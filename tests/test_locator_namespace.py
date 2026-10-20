"""Actual SDK public API namespace regression; synthetic locators are not live fixtures."""
import hashlib
import json
import re
import pytest
from test_crosswalk import deploy, spec


def locator(repo, filename='document.json'):
    return 'https://raw.githubusercontent.com/namespace-fixture/'+repo+'/'+'a'*40+'/'+filename


def submit(vm,c,repo,slot='source'):
    u=locator(repo)
    s=spec();s[slot]['url']=u
    c.register('ns',json.dumps(s,ensure_ascii=False))


@pytest.mark.parametrize('slot',['source','target'])
@pytest.mark.parametrize('repo',['.','..'])
def test_repository_dot_segments_are_rejected(direct_vm,direct_deploy,repo,slot):
    c=deploy(direct_vm,direct_deploy)
    with direct_vm.expect_revert('commit-pinned'):
        submit(direct_vm,c,repo,slot)


@pytest.mark.parametrize('repo',['.github','repo.name','_repo'])
def test_valid_repository_names_remain_accepted(direct_vm,direct_deploy,repo):
    c=deploy(direct_vm,direct_deploy)
    submit(direct_vm,c,repo)
