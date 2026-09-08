"""One-time, auditable reset requested on 2026-09-08. Not framework runtime."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / '.ai/archive/2026-09-08'

def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')

def dump(path, value):
    write(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))

def move(source, destination):
    source, destination = ROOT / source, ROOT / destination
    for path in (source, destination):
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Outside repository: {path}')
    if not source.exists():
        return
    if destination.exists():
        raise ValueError(f'Refusing overwrite: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
    except PermissionError:
        if not source.is_dir():
            raise
        destination.mkdir(exist_ok=True)
        for child in list(source.iterdir()):
            move(child.relative_to(ROOT), (destination/child.name).relative_to(ROOT))
        try:
            source.rmdir()
        except OSError:
            pass  # An empty directory may still be held by another reader.

if (ROOT/'.ai/STATE.yaml').exists():
    raise SystemExit('Reset already recorded; refusing to repeat')
files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
manifest = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files if p and (ROOT/p).is_file()}
tasks = []
for path in sorted((ROOT/'.ai/plans/current/PLAN-001/tasks/current').glob('*.json')):
    value = json.loads(path.read_text())
    tasks.append({'id': value['id'], 'title': value['title'], 'previous_status': value['status'], 'disposition': 'historical-completed' if value['status']=='accepted' else 'superseded'})
worktrees = []
for block in subprocess.check_output(['git','worktree','list','--porcelain'], cwd=ROOT, text=True).strip().split('\n\n'):
    values = dict(line.split(' ',1) for line in block.splitlines() if ' ' in line)
    path = Path(values['worktree']).resolve()
    if path == ROOT:
        continue
    if not path.is_relative_to((ROOT/'.worktrees').resolve()):
        raise ValueError(f'Unexpected worktree: {path}')
    status = subprocess.check_output(['git','-C',str(path),'status','--porcelain','--untracked-files=all'], text=True)
    ignored = subprocess.check_output(['git','-C',str(path),'ls-files','--others','--ignored','--exclude-standard'], text=True).splitlines()
    branch = values.get('branch','')
    if status or not branch or any('__pycache__/' not in p or not p.endswith('.pyc') for p in ignored):
        raise ValueError(f'Worktree requires preservation review: {path}')
    worktrees.append({'path':path.relative_to(ROOT).as_posix(),'branch':branch,'head':values['HEAD'],'merged':subprocess.run(['git','merge-base','--is-ancestor',values['HEAD'],'HEAD'],cwd=ROOT).returncode==0,'disposition':'superseded; branch retained; clean checkout removable','ignored_files':ignored})
dump('.ai/archive/2026-09-08/original-files.yaml', {'baseline_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'sha256':manifest})
dump('.ai/archive/2026-09-08/disposition.yaml', {'date':'2026-09-08','superseded_by':'PLAN-002','tasks':tasks,'worktrees':worktrees})
move('.ai/plans/current/PLAN-001','.ai/plans/superseded/PLAN-001')
for p in ['STATE.json','framework.json','AGENTS.md','README.md','ROADMAP.md','shared','project','research','decisions']:
    move('.ai/'+p,'.ai/archive/2026-09-08/workflow/'+p)
for p in ['docs','schemas','tests']:
    move(p,'.ai/archive/2026-09-08/legacy/'+p)
for p in files:
    if p.startswith('src/') and (ROOT/p).is_file():
        move(p,'.ai/archive/2026-09-08/legacy/'+p)
for p in ['README.md','ARCHITECTURE.md','CONTRIBUTING.md','SECURITY.md','pyproject.toml']:
    write('.ai/archive/2026-09-08/legacy/'+p,(ROOT/p).read_text(encoding='utf-8'))
for wt in worktrees:
    subprocess.run(['git','worktree','remove',str(ROOT/wt['path'])],cwd=ROOT,check=True)
dump('.ai/archive/2026-09-08/worktree-cleanup.yaml', {'removed':worktrees,'branches_deleted':[],'reason':'User explicitly superseded task-level execution; all files committed, branches retained, ignored files only bytecode.'})
write('.ai/plans/superseded/PLAN-001/SUPERSEDED.md', '# PLAN-001 — superseded on 2026-09-08\n\nPLAN-002 replaces this entire bundle. All original records, including embedded running statuses and old references, are immutable historical evidence and must never be executed. Fifteen accepted tasks remain completed historical work; all other tasks and graphs are superseded. See `.ai/archive/2026-09-08/disposition.yaml` for every task and retained worktree branch.\n')
write('.ai/archive/2026-09-08/README.md', '# Framework reset archive\n\nHistorical evidence only. Today\'s requirements supersede the old task-per-worktree engine, provider-specific namespaces, JSON record schemas, flat packaging, 22-role catalog, and multiple review contracts. PLAN-001 is preserved under `.ai/plans/superseded/PLAN-001/`. Original file hashes and per-task/worktree dispositions accompany this archive. No branch or commit was deleted.\n\nCompatible mechanisms to carry forward: explicit argv with no shell; timeouts and process cleanup; path containment and symlink rejection; bounded command evidence; immutable review attempts; dependency cycle detection and file/resource ownership checks; safe idempotent installation; configurable providers; serialized state writes. Reuse their algorithms and regression cases while removing legacy record coupling. Old source and tests are retained here for comparison, excluded from current packaging and test discovery. ADR-005\'s ownership/provider boundaries remain conceptually valid; ADR-001 through ADR-004 are superseded by ADR-006. Protocol research is retained with its original dates and uncertainties.\n')
write('.ai/decisions/ADR-006.md', '# ADR-006 — Feature orchestration and readable state\n\nStatus: accepted, 2026-09-08. Supersedes ADR-001 through ADR-004 and conflicting portions of ADR-005 in the reset archive. Authority: today\'s user request and Git Repo Layouts project discussion.\n\nUse a Python 3.11+ package, `.ai/STATE.yaml` as the workflow index, Markdown artifacts with YAML metadata, and `.ai/` for all providers. Tasks are planning units; feature batches own worktrees and implementation sessions. Decomposition validates both task and feature DAGs and serializes shared file/schema/interface ownership. One independent Critical Change Reviewer evaluates the full changed diff for correctness, relevant security, and documentation. Recovery repairs structure and redecomposes automatically; ordinary defects return to the same implementer. Bugs get a smaller investigation/fix/review route.\n\nGit remains authoritative for branches, commits and worktrees. A coordinator serializes state mutations with atomic writes and a local lock. No hosted database, event-sourcing system, dual reviews, task-per-agent rule, or mandatory plan integration review. Keep bounded retry budgets and explicit external-action permissions. Templates and model profiles are separate from agent behavior. Provider execution requires configured adapters; never report a simulated run as real work.\n')
write('.ai/research/archived/RES-001.md', '# RES-001 — Foundational protocol references\n\nPreserved factual research, originally recorded 2026-09-05. Git worktree porcelain inspection and Python argument-list subprocess execution remain relevant. The original source URLs, evidence notes, and unverified platform assumptions are preserved in `.ai/archive/2026-09-08/workflow/research/RES-001.json`. JSON Schema evidence is historical; it no longer defines current project records.\n')
dump('.ai/STATE.yaml', {'project':{'name':'ai-engineering-framework','framework_version':'0.2.0','phase':'planning'},'current_focus':{'plan':'PLAN-002'},'active_features':[],'waiting_features':[],'blocked_features':[],'open_bugs':[],'worktrees':[],'reviews':{},'pull_requests':{},'active_runs':[],'blockers':[],'next_actions':['Approve PLAN-002 decomposition before runtime implementation'],'generation':1})
print('Reset complete:',len(tasks),'historical task dispositions;',len(worktrees),'clean superseded worktrees removed; all branches retained.')
