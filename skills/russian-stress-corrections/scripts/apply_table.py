import re,sys,glob
B,TF=sys.argv[1],sys.argv[2]
T=[l.rstrip('\n').split('|') for l in open(TF,encoding='utf-8') if l.strip()]
files={};err=[];log=[]
for pos,old,new in T:
    c,l=pos.split(':');fn=f'{B}/roles_full-ch{c}.md'
    L=files.setdefault(fn,open(fn,encoding='utf-8').read().split('\n'))
    raw=L[int(l)-1];m=[i for i,ch in enumerate(raw) if ch!='+'];clean=''.join(raw[i] for i in m)
    k=clean.find(old)
    if k<0 or clean.find(old,k+1)>=0: err.append(f'{pos} {old!r} k={k}');continue
    rs=m[k];re_=m[k+len(old)-1]+1
    L[int(l)-1]=raw[:rs]+new+raw[re_:];log.append(f'ch{pos}: {old} -> {new.replace("+","")}')
if err: print('ABORT',*err,sep='\n');sys.exit(1)
for fn,L in files.items(): open(fn,'w',encoding='utf-8').write('\n'.join(L))
print(len(log),'applied');print(*log,sep='\n')
