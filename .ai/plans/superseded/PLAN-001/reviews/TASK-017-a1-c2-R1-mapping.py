"""Independent real-loader mapped-profile sequential-process recovery reproduction."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
ROOT=Path(__file__).resolve().parents[5]
CANDIDATE=ROOT/'.worktrees/TASK-017-a1'
REPORT=Path(__file__).with_suffix('.txt')
sys.path.insert(0,str(CANDIDATE/'src'))
sys.path.insert(1,str(CANDIDATE/'tests/unit/agents'))
import agents, config
from test_agents import capabilities, request
from domain_values import DomainException

if len(sys.argv)>1 and sys.argv[1]=='child':
    project=Path(sys.argv[2]); state=project/'state.json'
    s=config.load_project_settings(project,config.load_installation_record(project))
    r=request()
    facts={'runtime':platform.python_version(),'origin':agents.__file__,'policy_profile':r.model_profile,'configured_profile':s.configured_model(r.model_profile).name,'settings_sha256':hashlib.sha256((project/'.ai/project/policy.json').read_bytes()+(project/'.ai/project/agent-models.json').read_bytes()).hexdigest()}
    try:
        p=agents.FakeAgentProviderState(state)
        a=agents.DeterministicFakeAgentAdapter(project_id='project-1',settings=s,capabilities=capabilities(s,model_profiles=s.models.provider().profiles),provider_state=p)
        h=a.start(r,r.idempotency_key)
        assert a.start(r,r.idempotency_key)==h
        facts.update(outcome='started',effect_count=p.effect_count,handle=h.external_handle,poll=a.poll(h).status.value)
    except DomainException as exc:
        facts.update(outcome='rejected',category=exc.category.value,message=str(exc))
    print(json.dumps(facts)); sys.exit(0)

lines=['Harness setup note: first probe selected providers[0] through the owned helper, which is anthropic in real decoded settings; corrected to the active provider. A first alias choice to implementation_escalated violated the inactive Anthropic review rank constraint and never reached dispatch; the final fixture adds a distinct name for each existing provider implementation profile and its implementation model/rank, which both accepted configuration decoders admit.', f'Independent mapped-profile recovery; candidate={CANDIDATE}; runtime={sys.version}; origin={agents.__file__}']
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c2-R1-mapping-fixture-',dir=REPORT.parent) as temp:
    fixture=Path(temp)
    shutil.copytree(CANDIDATE/'schemas/v1',fixture/'schemas/v1')
    (fixture/'.ai/project').mkdir(parents=True)
    shutil.copyfile(CANDIDATE/'.ai/framework.json',fixture/'.ai/framework.json')
    models=json.loads((CANDIDATE/'.ai/project/agent-models.json').read_text())
    policy=json.loads((CANDIDATE/'.ai/project/policy.json').read_text())
    for provider in models['providers'].values():
        provider['profiles']['implementation_custom']=copy.deepcopy(provider['profiles']['implementation'])
    for alias in (False,True):
        models['policy_profile_map']['implementation']='implementation_custom' if alias else 'implementation'
        selected=models['providers']['openai']['profiles'][models['policy_profile_map']['implementation']]
        for p in policy['model_profiles']:
            if p['name']=='implementation':
                p.update(configured=True,provider='OpenAI',model_id=selected['model_id'],capability_rank=selected['capability_rank'])
            if p['name']=='review_high': p['configured']=True
        (fixture/'.ai/project/agent-models.json').write_text(json.dumps(models),encoding='utf-8')
        (fixture/'.ai/project/policy.json').write_text(json.dumps(policy),encoding='utf-8')
        (fixture/'state.json').unlink(missing_ok=True)
        runs=[]
        for _ in range(2):
            result=subprocess.run([sys.executable,'-B',str(Path(__file__)),'child',str(fixture)],cwd=CANDIDATE,capture_output=True,text=True,shell=False)
            assert result.returncode==0,result.stderr
            runs.append(json.loads(result.stdout))
        assert runs[0]['outcome']=='started' and runs[0]['effect_count']==1
        assert runs[0]['settings_sha256']==runs[1]['settings_sha256']
        if alias:
            assert runs[1]['outcome']=='rejected' and runs[1]['category']=='validation_failed'
        else:
            assert runs[1]['outcome']=='started' and runs[1]['handle']==runs[0]['handle'] and runs[1]['effect_count']==1
        lines.append(('MAPPED valid profile' if alias else 'IDENTITY profile control')+': '+json.dumps(runs,sort_keys=True))
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
