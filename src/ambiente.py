"""Instalação automática das dependências declaradas, no Python do notebook."""
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import importlib
import os
import subprocess
import sys

RAIZ=Path(__file__).resolve().parents[1]

def garantir_dependencias(processamento=False):
    # Os percursos já vêm calculados em data/processed/; não há dependências
    # extras de processamento na entrega. O argumento é mantido por compatibilidade.
    arquivos=[RAIZ/'requirements.txt']
    try:
        from packaging.requirements import Requirement
    except ImportError:
        if os.environ.get('AEDV_INSTALAR_DEPENDENCIAS','1')=='0':
            raise RuntimeError('Instale as dependências com python -m pip install -r requirements.txt.')
        subprocess.run([sys.executable,'-m','pip','install','packaging>=24'],check=True)
        from packaging.requirements import Requirement
    faltando=[]
    for arquivo in arquivos:
        for linha in arquivo.read_text(encoding='utf-8-sig').splitlines():
            linha=linha.split('#',1)[0].strip()
            if not linha or linha.startswith('-r'): continue
            req=Requirement(linha)
            if req.marker and not req.marker.evaluate(): continue
            try: instalada=version(req.name)
            except PackageNotFoundError: instalada=None
            if instalada is None or instalada not in req.specifier: faltando.append(str(req))
    if faltando:
        if os.environ.get('AEDV_INSTALAR_DEPENDENCIAS','1')=='0':
            raise RuntimeError('Dependências ausentes/incompatíveis: '+', '.join(faltando))
        aliases={'ipython':'IPython','pyyaml':'yaml','pillow':'PIL'}
        ja_carregados=[r for r in faltando if aliases.get(Requirement(r).name.lower(),Requirement(r).name.replace('-','_')) in sys.modules]
        print('Preparando dependências do projeto:',', '.join(faltando))
        subprocess.run([sys.executable,'-m','pip','install',*faltando],check=True)
        importlib.invalidate_caches()
        if ja_carregados:
            raise RuntimeError('Dependências atualizadas. Reinicie o kernel e execute novamente.')
