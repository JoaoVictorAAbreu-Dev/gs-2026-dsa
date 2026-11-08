"""Gera docs/Sintese_Executiva_Cantareira.pdf (1 página) a partir de reports/results.json e dos dados.

Execute depois do notebook: python scripts/build_executive_summary.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import hydro  # noqa: E402

OUT = ROOT / "docs" / "Sintese_Executiva_Cantareira.pdf"
AZUL = colors.HexColor("#0d47a1")

# Fonte TrueType com glifos de "³", "≤" e "−" (Liberation Sans, métrica compatível com Arial)
_FONTES = Path("/usr/share/fonts/truetype/liberation")
try:
    pdfmetrics.registerFont(TTFont("Sans", str(_FONTES / "LiberationSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Sans-Bold", str(_FONTES / "LiberationSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold")
    REG, BOLD = "Sans", "Sans-Bold"
except Exception:  # fonte ausente: usa Helvetica (alguns símbolos podem não aparecer)
    REG, BOLD = "Helvetica", "Helvetica-Bold"

base = ParagraphStyle("b", fontName=REG, fontSize=8.2, leading=10.4, alignment=TA_LEFT, spaceAfter=2)
h = ParagraphStyle("h", parent=base, fontName=BOLD, fontSize=9.2, textColor=AZUL, spaceBefore=4, spaceAfter=1.5)
titulo = ParagraphStyle("t", parent=base, fontName=BOLD, fontSize=13, leading=15, textColor=AZUL)
sub = ParagraphStyle("s", parent=base, fontSize=8, textColor=colors.HexColor("#424242"))


def grafico() -> io.BytesIO:
    df = hydro.load_series()
    fig, ax = plt.subplots(figsize=(7.4, 1.75))
    cores = {1: "#2e7d32", 2: "#f9a825", 3: "#ef6c00", 4: "#c62828", 5: "#6a1b9a"}
    for numero, nome, lim in hydro.FAIXAS:
        sup = 100 if numero == 1 else hydro.limite_inferior(numero - 1)
        ax.axhspan(lim, sup, color=cores[numero], alpha=0.12)
        ax.text(df.date.iloc[-1], (lim + min(sup, 82)) / 2, f"  F{numero} {nome}", fontsize=6, va="center",
                color=cores[numero])
    ax.plot(df.date, df.storage_pct, color="#0d47a1", lw=1.4)
    ax.set_ylim(0, 82); ax.set_ylabel("Volume útil (%)", fontsize=7)
    ax.tick_params(labelsize=6.5); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Cantareira — volume útil diário (Sabesp) e faixas de operação ANA/DAEE 925/2017", fontsize=7.5)
    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220)
    plt.close(fig)
    buf.seek(0)
    return buf


def main() -> None:
    r = json.loads((ROOT / "reports" / "results.json").read_text(encoding="utf-8"))
    sit = {k: re.sub(r"(\d)\.(\d)", r"\1,\2", v) if k != "data de referência" else v
           for k, v in r["situacao_atual"].items()}
    reg = {(x["horizonte"], x["modelo"]): x["MAE"] for x in r["regressao"]}
    clf = {x["modelo"]: x for x in r["classificacao"]}
    lr, rf, regra = clf["Regressão Logística"], clf["Random Forest"], clf["Regra de autonomia"]
    num = lambda v, d=2: f"{v:.{d}f}".replace(".", ",")  # noqa: E731

    story = [
        Paragraph("Síntese executiva — Risco hídrico no Sistema Cantareira (RMSP)", titulo),
        Paragraph("Global Solution 2026.2 · Data Science and Analytics · FIAP — <b>Integrantes:</b> João Victor Alves de Abreu "
                  "(RM 564946) e Rodrigo Kenshin Viana Matayoshi (RM 564026)", sub),
        Spacer(1, 3),
        Paragraph("Problema e pergunta", h),
        Paragraph("A retirada de água do Cantareira, maior produtor da RMSP, é limitada por <b>faixas de operação</b> definidas pelo "
                  "volume útil (Resolução ANA/DAEE 925/2017). Entrar em uma faixa mais restritiva exige preparo da gestão. "
                  "<b>Pergunta:</b> com dados publicados até hoje, é possível sinalizar com até 30 dias de antecedência a entrada em "
                  "uma faixa mais restritiva?", base),
        Paragraph("Dados", h),
        Paragraph(f"Portal dos Mananciais (Sabesp), série diária de {r['periodo'][0]} a {r['periodo'][1]} ({r['dias']} dias): volume "
                  "útil (%), chuva (mm), vazão natural afluente e vazão produzida (m³/s). Sem lacunas, duplicidades ou ajustes; o trecho "
                  "2024–2025 confere com uma extração anterior independente. Limites: um único sistema, sem vazão de jusante, endpoint "
                  "não documentado.", base),
        Image(grafico(), width=180 * mm, height=42.5 * mm),
        Paragraph("Indicadores", h),
        Paragraph("<b>I1</b> volume útil e faixa · <b>I2</b> tendência de 30 dias (p.p.) · <b>I3</b> balanço parcial = afluência − "
                  "produção, média de 30 dias (m³/s) · <b>I4</b> chuva acumulada de 30 dias (mm) · <b>I5</b> autonomia: dias até o "
                  "limite da faixa se o ritmo de queda continuar. Nas seis mudanças para faixa pior do período, o I5 ficou abaixo de "
                  "30 dias entre 24 e 29 dias antes da mudança.", base),
        Paragraph("Modelos e resultados (validação walk-forward, 7 janelas trimestrais, jan/2025–set/2026)", h),
    ]
    tabela = [
        ["Tarefa", "Modelo", "Resultado", "Leitura"],
        ["Piora de faixa\nem 30 dias", "Regressão Logística", f"recall {num(lr['recall'])} · precisão {num(lr['precisão'])}\nAUC {num(lr['AUC'])} · F2 {num(lr['F2'])}",
         "Melhor modelo; antecipa a maioria\ndos dias que precedem uma piora"],
        ["", "Random Forest", f"recall {num(rf['recall'])} · precisão {num(rf['precisão'])}", "Conservador: poucos episódios\npara aprender"],
        ["", "Regra de autonomia (I5 ≤ 30 d)", f"recall {num(regra['recall'])} · precisão {num(regra['precisão'])}", "Referência simples e auditável"],
        ["Variação do\nvolume (MAE, p.p.)", "Ridge · Random Forest", f"7 dias: {num(reg[(7, 'Ridge')])} · {num(reg[(7, 'Random Forest')])}\n"
         f"30 dias: {num(reg[(30, 'Ridge')])} · {num(reg[(30, 'Random Forest')])}",
         f"Em 30 dias, não superam a tendência\n({num(reg[(30, 'Tendência 30d')])}): o volume depende da chuva futura"],
    ]
    t = Table(tabela, colWidths=[24 * mm, 42 * mm, 54 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), REG, 7.2), ("FONT", (0, 0), (-1, 0), BOLD, 7.4),
        ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
        ("SPAN", (0, 1), (0, 3)), ("BACKGROUND", (1, 1), (-1, 1), colors.HexColor("#e3f2fd")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
    ]))
    story += [
        t,
        Paragraph("Situação em " + sit["data de referência"] + " e alerta", h),
        Paragraph(f"Volume {sit['volume útil']} — <b>faixa {sit['faixa de operação']}</b>; tendência {sit['tendência 30 dias']} e "
                  f"balanço {sit['balanço parcial 30 dias']}; probabilidade de piora em 30 dias: {sit['probabilidade de piora de faixa (30 dias)']}. "
                  f"<b>Nível de alerta: {sit['NÍVEL DE ALERTA'].upper()}</b> (pela faixa atual, sem sinal de piora). Projeção em 30 dias: "
                  f"{sit['projeção de volume em 30 dias (tendência)']} — incerteza alta na estação chuvosa. Critério: Normal = faixa 1; "
                  "Atenção = faixa 2; Alerta = faixa 3; Crítico = faixas 4–5; o nível sobe um degrau se houver sinal de piora.", base),
        Paragraph("Recomendações (para avaliação dos gestores)", h),
        Paragraph("1) Tratar o volume no fim de março como indicador-chave: de abril a setembro o sistema perde de 1,5 a 5 p.p. por mês. "
                  "2) A partir de abril, acompanhar semanalmente a autonomia (I5); abaixo de 30 dias, preparar comunicação e planos da "
                  "faixa seguinte. 3) Incorporar previsão sazonal de chuva e vazão de jusante antes de publicar previsões de volume. "
                  "4) Estender a análise aos demais sistemas da RMSP.", base),
        Paragraph("Responsabilidade", h),
        Paragraph("Os alertas são recomendações para avaliação humana; não confirmam crise nem autorizam racionamento. Amostra curta "
                  "(menos de 3 anos, 6 mudanças de faixa); sem dados pessoais; análise reproduzível no notebook do projeto.", base),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=11 * mm,
                            bottomMargin=9 * mm, title="Síntese executiva — Cantareira",
                            author="João Victor Alves de Abreu; Rodrigo Kenshin Viana Matayoshi")
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
