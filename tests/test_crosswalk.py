import json
from pathlib import Path
import re
import pytest

ROOT=Path(__file__).parents[1]
CONTRACT=str(ROOT/'unit_safe_crosswalk.py')
SOURCES=json.loads((ROOT/'fixtures/sources.json').read_text())
BODIES=[(ROOT/'fixtures'/s['file']).read_text(encoding='utf-8') for s in SOURCES]
SQ='It sets the maximum time in seconds'
TQ='It sets the maximum time in milliseconds'

def deploy(vm,deploy):
    vm.warp('2026-10-21T00:00:00Z')
    return deploy(CONTRACT,sdk_version='v0.2.12')

def spec(reverse=False):
    a,b=(1,0) if reverse else (0,1)
    return {'source':{'url':SOURCES[a]['url'],'sha256':SOURCES[a]['sha256']},'target':{'url':SOURCES[b]['url'],'sha256':SOURCES[b]['sha256']},'pairs':[{'source_field':'CURLOPT_CONNECTTIMEOUT_MS' if reverse else 'CURLOPT_CONNECTTIMEOUT','target_field':'CURLOPT_CONNECTTIMEOUT' if reverse else 'CURLOPT_CONNECTTIMEOUT_MS','source_unit':'ms' if reverse else 's','target_unit':'s' if reverse else 'ms','source_min':1,'source_max':3600000 if reverse else 3600,'target_min':1,'target_max':3600 if reverse else 3600000}]}

def serve(vm,changed=False):
    for i,s in enumerate(SOURCES):
        vm.mock_web(re.escape(s['url']),{'status':200,'body':'changed bytes' if changed else BODIES[i]})

def model(vm,decision='MATCH',sq=SQ,tq=TQ,reverse=False):
    if reverse: sq,tq=tq,sq
    vm.mock_llm('UNIT_SAFE_CROSSWALK_V1',json.dumps({'assessments':[{'decision':decision,'source_quote':sq,'target_quote':tq}]}))

def locked(vm,c,reverse=False):
    c.register('curl',json.dumps(spec(reverse)))
    serve(vm);model(vm,reverse=reverse)

def approved(vm,c,reverse=False):
    locked(vm,c,reverse);c.assess('curl')

def test_real_documents_consensus_and_exact_transform(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c)
    assert c.get_adapter('curl')['status']=='APPROVED'
    assert c.transform('curl','{"CURLOPT_CONNECTTIMEOUT": 2}')=={'CURLOPT_CONNECTTIMEOUT_MS':2000}
    assert direct_vm.run_validator() is True
    direct_vm.clear_mocks();serve(direct_vm,True);model(direct_vm)
    assert direct_vm.run_validator() is False

def test_independent_semantic_disagreement_rejected(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c)
    direct_vm.clear_mocks();serve(direct_vm);model(direct_vm,'UNCERTAIN')
    assert direct_vm.run_validator() is False

def test_forged_leader_quote_rejected(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c)
    packet=c.get_adapter('curl')['assessment']
    packet['assessments'][0]['source_quote']='fabricated quotation not in curl documentation'
    assert direct_vm.run_validator(leader_result=packet) is False

def test_fractional_integer_conversion_is_rejected(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c,True)
    assert c.transform('curl','{"CURLOPT_CONNECTTIMEOUT_MS": 2000}')=={'CURLOPT_CONNECTTIMEOUT':2}
    with direct_vm.expect_revert('fractional'):
        c.transform('curl','{"CURLOPT_CONNECTTIMEOUT_MS": 1500}')

@pytest.mark.parametrize('payload',['{"CURLOPT_CONNECTTIMEOUT": true}','{"CURLOPT_CONNECTTIMEOUT": 0}','{"CURLOPT_CONNECTTIMEOUT": 3601}','{"CURLOPT_CONNECTTIMEOUT": 1.5}','{"CURLOPT_CONNECTTIMEOUT": 2, "extra":1}','{}','{"CURLOPT_CONNECTTIMEOUT":1,"CURLOPT_CONNECTTIMEOUT":2}'])
def test_strict_payload_and_domain(direct_vm,direct_deploy,payload):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c)
    with direct_vm.expect_revert(): c.transform('curl',payload)

@pytest.mark.parametrize('decision,status',[('DIFFERENT','REJECTED'),('UNCERTAIN','UNCERTAIN')])
def test_no_reroll_and_no_transform_without_match(direct_vm,direct_deploy,decision,status):
    c=deploy(direct_vm,direct_deploy);locked(direct_vm,c);direct_vm.clear_mocks();serve(direct_vm);model(direct_vm,decision)
    c.assess('curl');assert c.get_adapter('curl')['status']==status
    with direct_vm.expect_revert('already assessed'): c.assess('curl')
    with direct_vm.expect_revert('not approved'): c.transform('curl','{"CURLOPT_CONNECTTIMEOUT": 2}')
    with direct_vm.expect_revert('fingerprint'): c.register('retry',json.dumps(spec()))

def test_bijection_and_unit_dimensions_locked(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy)
    s=spec();s['pairs'][0]['target_unit']='KiB'
    with direct_vm.expect_revert('dimension'): c.register('bad',json.dumps(s))
    s=spec();s['pairs'].append(dict(s['pairs'][0]))
    with direct_vm.expect_revert('bijection'): c.register('bad',json.dumps(s))
    s=spec();s['pairs'][0]['source_min']=0
    with direct_vm.expect_revert('positive'): c.register('bad',json.dumps(s))

def test_owner_access_and_terminal_revocation(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);approved(direct_vm,c)
    from gltest.direct import create_address
    with direct_vm.prank(create_address('other')):
        with direct_vm.expect_revert('owner only'): c.revoke('curl')
        with direct_vm.expect_revert('owner only'): c.register('other',json.dumps(spec()))
    c.revoke('curl');assert c.get_adapter('curl')['status']=='REVOKED'
    with direct_vm.expect_revert('not approved'): c.transform('curl','{"CURLOPT_CONNECTTIMEOUT": 2}')
    with direct_vm.expect_revert('already assessed'): c.assess('curl')

def test_source_pinning_and_hash_checked_at_assessment(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);s=spec();s['source']['url']=s['source']['url'].replace('8f143e852f2c5ef5a10a9af20ac04617e5dfef83','main')
    with direct_vm.expect_revert('commit-pinned'): c.register('bad',json.dumps(s))
    locked(direct_vm,c);direct_vm.clear_mocks();serve(direct_vm,True);model(direct_vm)
    with direct_vm.expect_revert('SOURCE'): c.assess('curl')
    assert c.get_adapter('curl')['status']=='LOCKED'

def test_invalid_model_schema_and_quote(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);locked(direct_vm,c)
    direct_vm.clear_mocks();serve(direct_vm);model(direct_vm,sq='injected quotation never present')
    with direct_vm.expect_revert('MODEL'): c.assess('curl')

def test_pair_order_cannot_reroll_same_correspondences(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);s=spec()
    second=dict(s['pairs'][0],source_field='second_source',target_field='second_target')
    s['pairs'].append(second);c.register('one',json.dumps(s))
    s['pairs'].reverse()
    with direct_vm.expect_revert('fingerprint'): c.register('two',json.dumps(s))
