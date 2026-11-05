"""Render a one-page executive summary from local exploratory results."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports/results.json"
OUT = ROOT / "deliverables/GS2026_DSA_ExecutiveSummary.pdf"


def wrapped(pdf: canvas.Canvas, text: str, x: float, y: float, width: float, *, size=10.5, leading=16):
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, "Helvetica", size) > width and line:
            pdf.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = candidate
    if line:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def main():
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    horizons = {"1": {"metrics": result["metrics"]}, "7": result["seven_day_horizon"]}
    bt1 = result["backtest"]["one_day"]["folds_beating_persistence"]
    bt7 = result["backtest"]["seven_day"]["folds_beating_persistence"]
    bias7 = {k: v["bias_percentage_points"] for k, v in result["seven_day_horizon"]["metrics"].items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUT), pagesize=A4)
    width, height = A4
    margin = 45
    ink = HexColor("#17324D")
    accent = HexColor("#087E8B")
    muted = HexColor("#526477")
    pdf.setFillColor(ink)
    pdf.rect(0, height - 96, width, 96, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(margin, height - 48, "Cantareira: previsão com limites claros")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(margin, height - 68, "FIAP Global Solution 2026.2  |  Data Science and Analytics  |  05/11/2026")
    y = height - 126

    def section(title: str, body: str, y: float) -> float:
        pdf.setFillColor(accent)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(margin, y, title)
        y -= 17
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica", 10.5)
        return wrapped(pdf, body, margin, y, width - 2 * margin)

    y = section("Pergunta e dados", "Com que erro podemos estimar o volume útil (%) do Sistema Cantareira em 1 e 7 dias, usando apenas dados já publicados? Foram analisados 731 registros diários de 2024 a 2025 do Portal dos Mananciais Sabesp. O recorte não representa toda a RMSP e não prevê falta de água por bairro.", y)
    y -= 8
    y = section("Método", "Treino com alvos anteriores a 01/07/2025; teste com 184 alvos de julho a dezembro de 2025. Sem embaralhamento temporal. Entradas disponíveis até a data da previsão: volume atual e histórico recente, chuva observada e acumulada. Ridge e Random Forest aprendem a variação do volume e são comparados à persistência; MAE em pontos percentuais. Backtest em cinco janelas de três meses (out/2024 a dez/2025).", y)
    y -= 11
    pdf.setFillColor(accent)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y, "Resultados no período de teste")
    y -= 19
    col = [margin, margin + 105, margin + 220, margin + 335]
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica-Bold", 9)
    for x, label in zip(col, ["Horizonte", "Persistência", "Ridge", "Random Forest"]):
        pdf.drawString(x, y, label)
    y -= 15
    pdf.setFillColor(ink)
    pdf.setFont("Helvetica", 9)
    for key, label in [("1", "1 dia"), ("7", "7 dias")]:
        metrics = horizons[key]["metrics"]
        values = [label] + [f'{metrics[name]["mae_percentage_points"]:.3f} pp' for name in ["persistence", "ridge", "random_forest"]]
        for x, value in zip(col, values):
            pdf.drawString(x, y, value)
        y -= 16
    y -= 9
    y = section("Interpretação", f"Ridge venceu a persistência em {bt1['ridge']}/5 janelas (1 dia) e {bt7['ridge']}/5 (7 dias); Random Forest em {bt1['random_forest']}/5 e {bt7['random_forest']}/5. Em 7 dias os modelos foram otimistas na queda (viés Ridge {bias7['ridge']:+.2f} pp): superestimar água é o erro mais grave, pois gera falsa tranquilidade. Erro baixo em 1 dia reflete a mudança lenta do reservatório, não antecipação de eventos críticos.", y)
    y -= 8
    y = section("Decisão responsável", "Não usar os modelos para alerta público ou racionamento. Próximos passos: estimar intervalos de incerteza, conferir semântica e horário das medições, incorporar outros sistemas, definir limiares com base oficial e submeter qualquer mensagem à revisão humana.", y)
    y -= 12
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 8)
    y = wrapped(pdf, "Fonte: mananciais.sabesp.com.br/base-dados. Endpoint observado no site; estabilidade e licença de redistribuição ainda não confirmadas. Dados e notebook executado permanecem locais. Integrantes e RMs: preencher antes da entrega.", margin, y, width - 2 * margin, size=8, leading=11)
    if y < 40:
        raise RuntimeError("Executive summary overflowed the page")
    pdf.showPage()
    pdf.save()
    print(OUT)


if __name__ == "__main__":
    main()
