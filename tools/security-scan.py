#!/usr/bin/env python3
"""Safety net, not a comprehensive secret scanner. Does not inspect Git history."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
issues=[]
SKIP={'.git','.gradle','.gradle-pitv','.idea','build','__pycache__','node_modules','release-archives'}
BLOCKED={'api-token','remote-token','tls-key.pem','local.properties','.env'}
for file in ROOT.rglob('*'):
    if not file.is_file() or any(x in SKIP for x in file.relative_to(ROOT).parts):continue
    rel=file.relative_to(ROOT)
    if file.name in BLOCKED or file.suffix in {'.apk','.jks','.keystore','.p12'}:issues.append((str(rel),'forbidden filename'));continue
    if file.stat().st_size>2_000_000:continue
    try:s=file.read_text(encoding='utf-8')
    except UnicodeDecodeError:continue
    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',s):issues.append((str(rel),'private key material'))
    if re.search(r'(?:Authorization\s*:\s*Bearer\s+)[A-Za-z0-9_\-.]{28,}',s,re.I):issues.append((str(rel),'hardcoded bearer token'))
    if re.search(r'(?:\?|&)key=[A-Za-z0-9_\-]{22,}',s):issues.append((str(rel),'fixed web remote token in URL'))
if issues:
    print('POSSIBLE SENSITIVE MATERIAL:')
    for f,reason in issues:print(' -',f,reason)
    sys.exit(1)
print('OK: No obvious secrets in tracked source files. Review Git history manually too.')
