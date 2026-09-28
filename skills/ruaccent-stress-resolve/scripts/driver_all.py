# All chapters 02-24: 3 runs each (new prompt), retry incomplete chunks, then vote + commit per chapter
import subprocess,os,re,threading,time
from concurrent.futures import ThreadPoolExecutor
W='/home/vellum/.local/share/vellum/assistants/juno/.vellum/workspace'
ST=W+'/art/new-books/stress'; R=W+'/narrator/reports/clockwork-rocket-stress'
os.makedirs(ST+'/logs',exist_ok=True)
CHS=[c for c in (f'{i:02d}' for i in range(2,25)) if c not in ['01','02','03','04','05','06','07']]
RUNS=['','2','3']
done={c:0 for c in CHS}; lock=threading.Lock()
def log(*a):
    with lock: print(time.strftime('%H:%M:%S'),*a,flush=True)
def one(ch,r):
    for att in range(4):
        env=dict(os.environ,RUN=r)
        if att==3: env['FINAL']='1'
        p=subprocess.run(['python3','resolve.py',ch],cwd=ST,env=env,capture_output=True,text=True)
        open(f'{ST}/logs/res-{ch}-{r or 1}.log','a').write(p.stdout+p.stderr)
        m=re.search(r"'noanswer': (\d+)",p.stdout)
        na=int(m.group(1)) if m else -1
        log('ch',ch,'run',r or 1,'att',att,'noanswer',na)
        if na==0: break
    with lock:
        done[ch]+=1; last=done[ch]==3
    if last:
        v=subprocess.run(['python3','vote.py',ch],cwd=ST,capture_output=True,text=True)
        log('VOTE ch',ch,v.stdout.split('\n')[0],v.stderr[-300:])
        with lock:
            subprocess.run(f'cp resolve.py vote.py {R}/; cd {W}/narrator && git add reports/clockwork-rocket-stress && git commit -q -m "clockwork-rocket ch{ch}: 3-run vote stress resolve" && GIT_SSH_COMMAND="ssh -i {W}/.ssh/id_ed25519 -o IdentitiesOnly=yes" git push -q origin HEAD',shell=True,cwd=ST)
jobs=[(c,r) for c in CHS for r in RUNS]
with ThreadPoolExecutor(1) as ex: list(ex.map(lambda j:one(*j),jobs))
log('ALL CHAPTERS DONE')
