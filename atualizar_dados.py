"""
atualizar_dados.py
──────────────────
Execute este script sempre que adicionar novos arquivos xlsx na pasta
Acompanhamento. Ele relê todos os arquivos, extrai o rendimento e
atualiza o data.json que o app usa.

Como usar:
  1. Coloque os novos arquivos na pasta Acompanhamento
  2. Abra o terminal nesta pasta e execute:
       python atualizar_dados.py
  3. Faça push para o GitHub — o app atualiza automaticamente.
"""

import os
import re
import json
from pathlib import Path

import pandas as pd

# ── Configuração ──────────────────────────────────────────────────────────────
PASTA_XLSX = Path(r"C:\Users\costa\OneDrive\Documentos\01_Profissional\Reservas_Flat\Acompanhamento")
SAIDA_JSON = Path(__file__).parent / "data.json"

UNIDADES = ["GV 402","GV 306","GV 305","PJ 204","CR 408",
            "T 801","T 3103","T 2807","Mercure","Puerto de Vilas","Puerto Bilbao"]

MESES_MAP = {
    "janeiro":1,"fevereiro":2,"março":3,"marco":3,
    "abril":4,"abrir":4,"maio":5,"junho":6,"julho":7,
    "agosto":8,"setembro":9,"setenbro":9,
    "outubro":10,"novembro":11,"novenbro":11,
    "dezembro":12,"dezemdro":12,
}

MESES_PT = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

# Palavras-chave que identificam rendimento líquido nas planilhas
TERMOS_RENDIMENTO = [
    "rendimento líquido", "rendimento liquido",
    "receita líquida", "receita liquida",
    "valor líquido", "valor liquido",
    "líquido", "liquido",
]

def parse_nome_arquivo(nome):
    n = nome.lower().replace(".xlsx", "")
    anos = re.findall(r"\b(20\d{2})\b", n)
    ano = int(anos[0]) if anos else None
    if not ano:
        m2 = re.findall(r"\b(1[89]|2[0-6])\b", n)
        if m2:
            ano = 2000 + int(m2[0])
    mes = None
    for m_str, m_num in MESES_MAP.items():
        if m_str in n:
            mes = m_num
            break
    return mes, ano

def extrair_rendimento_xlsx(caminho):
    """Tenta extrair o rendimento líquido de cada unidade em um arquivo xlsx."""
    try:
        xl = pd.ExcelFile(caminho, engine="openpyxl")
    except Exception as e:
        print(f"  ⚠ Não foi possível abrir: {e}")
        return {}

    resultado = {}

    for sheet in xl.sheet_names:
        nome_sheet = sheet.strip()
        # Verifica se o nome da aba corresponde a alguma unidade
        unidade = None
        for u in UNIDADES:
            if u.lower().replace(" ", "") in nome_sheet.lower().replace(" ", ""):
                unidade = u
                break
        if not unidade:
            continue

        try:
            df = xl.parse(sheet, header=None)
        except Exception:
            continue

        # Procura linha com termo de rendimento
        for i, row in df.iterrows():
            row_str = " ".join(str(c).lower() for c in row if pd.notna(c))
            if any(t in row_str for t in TERMOS_RENDIMENTO):
                # Pega o último valor numérico da linha
                nums = [c for c in row if isinstance(c, (int, float)) and not pd.isna(c)]
                if nums:
                    resultado[unidade] = float(nums[-1])
                    break

    return resultado

def main():
    print(f"📂 Lendo arquivos de: {PASTA_XLSX}\n")
    if not PASTA_XLSX.exists():
        print("❌ Pasta não encontrada. Verifique o caminho em PASTA_XLSX.")
        return

    registros = {}

    arquivos = sorted(PASTA_XLSX.glob("*.xlsx"))
    for arq in arquivos:
        if arq.name.startswith("~") or arq.name == "desktop.ini":
            continue

        mes, ano = parse_nome_arquivo(arq.name)
        if not mes or not ano:
            print(f"  ⚠ Ignorado (sem data clara): {arq.name}")
            continue

        chave = (ano, mes)
        if chave in registros:
            print(f"  ⚠ Duplicata ignorada: {arq.name}")
            continue

        print(f"  ✓ {MESES_PT[mes]}/{ano} — {arq.name}")
        valores = extrair_rendimento_xlsx(arq)

        registro = {
            "mes": MESES_PT[mes],
            "ano": ano,
            "n": mes,
        }
        for u in UNIDADES:
            registro[u] = valores.get(u, None)

        registros[chave] = registro

    # Ordena cronologicamente
    lista = [registros[k] for k in sorted(registros.keys())]

    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json atualizado com {len(lista)} meses.")
    print("   Próximo passo: git add data.json && git commit -m 'atualiza dados' && git push")

if __name__ == "__main__":
    main()
