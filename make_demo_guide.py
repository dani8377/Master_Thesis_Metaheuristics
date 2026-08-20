"""
Generates DEMO_GUIDE.pdf, the run sheet for the MSc defence software demo.

Master's thesis "Evaluation of Metaheuristic Algorithms for Energy Optimisation
in Scheduling and Routing".
Christian Wu (s194597) and Daniel Diamant (s205336)
Defence: 28 August 2026, DTU Lyngby, building 322 room 017.

Usage (from the project root):
    uv run --with reportlab python make_demo_guide.py

Writes DEMO_GUIDE.pdf next to this file.  Edit the CONTENT section below and
re-run to regenerate; the PDF is a build artefact of this script, not a
hand-made document.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, KeepTogether, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)

OUT = Path(__file__).parent / "DEMO_GUIDE.pdf"

# Okabe-Ito, matching the figures in the thesis
BLUE = colors.HexColor("#0072B2")
ORANGE = colors.HexColor("#E69F00")
RED = colors.HexColor("#D55E00")
GREEN = colors.HexColor("#009E73")
GREY = colors.HexColor("#F0F0F0")
DARK = colors.HexColor("#222222")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
_ss = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=_ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=16, leading=19, textColor=BLUE, spaceBefore=2,
                    spaceAfter=7)
H2 = ParagraphStyle("H2", parent=_ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=11.5, leading=14, textColor=DARK, spaceBefore=11,
                    spaceAfter=5)
BODY = ParagraphStyle("BODY", parent=_ss["BodyText"], fontName="Helvetica",
                      fontSize=9.3, leading=13, alignment=TA_LEFT,
                      spaceAfter=5, textColor=DARK)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8.2, leading=11)
CELL = ParagraphStyle("CELL", parent=BODY, fontSize=8.3, leading=10.8,
                      spaceAfter=0)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
CODE = ParagraphStyle("CODE", parent=BODY, fontName="Courier-Bold",
                      fontSize=9.6, leading=13.5, textColor=DARK,
                      spaceAfter=0, spaceBefore=0)
CODESM = ParagraphStyle("CODESM", parent=CODE, fontName="Courier",
                        fontSize=8.1, leading=11.5)


def code_block(lines: list[str], accent=BLUE):
    """A shaded, left-ruled block of literal commands.

    Uses Preformatted rather than Paragraph so the text in the PDF is plain
    ASCII with real spaces.  These commands are meant to be selected out of
    the PDF and pasted into a shell, so no &nbsp;, no smart quotes, no soft
    hyphens, and no line continuations that a copy would break.
    """
    style = CODE if max(len(x) for x in lines) < 62 else CODESM
    t = Table([[Preformatted("\n".join(lines), style)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LINEBEFORE", (0, 0), (0, -1), 2.6, accent),
    ]))
    return t


def table(header: list[str], rows: list[list[str]], widths: list[float],
          accent=BLUE):
    data = [[Paragraph(f"<b>{h}</b>", CELLB) for h in header]]
    data += [[Paragraph(c, CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return t


def callout(title: str, body: str, accent=RED):
    inner = [
        [Paragraph(f"<b>{title}</b>", ParagraphStyle(
            "ct", parent=CELL, fontName="Helvetica-Bold", textColor=accent,
            fontSize=9.3))],
        [Paragraph(body, CELL)],
    ]
    t = Table(inner, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8F2")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.6, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _chrome(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(MARGIN, 11 * mm,
                      "Software demo run sheet  |  Wu & Diamant  |  DTU defence, 28 Aug 2026")
    canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, f"{doc.page}")
    canvas.setStrokeColor(colors.HexColor("#DDDDDD"))
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# CONTENT
# ---------------------------------------------------------------------------
def build() -> None:
    s = []
    W = CONTENT_W

    # ---------------------------------------------------------------- page 1
    s.append(Paragraph("Software demo: run sheet", H1))
    s.append(Paragraph(
        "MSc defence, Friday 28 August 2026, 10:00-11:15, DTU Lyngby building 322 room 017. "
        "Joint presentation of max. 30 minutes, of which approx. 5 minutes is a live "
        "demonstration of the software. Christian Wu and Daniel Diamant, supervisor "
        "Professor Carsten Witt.", SMALL))

    s.append(Paragraph("1. The two commands", H2))
    s.append(Paragraph(
        "This is the entire demo. Everything else in this document is preparation "
        "or narration.", BODY))
    s.append(code_block([
        "cd ~/demo",
        "uv run run.py cloud -a SA GA UMDA greedy -s 1",
        "uv run run.py ev -a SA Greedy -s 1",
    ]))
    s.append(Spacer(1, 5))
    s.append(Paragraph(
        "<b>run.py</b> handles the difference between the two modules for you: the cloud "
        "module runs from its own directory, the EV module runs from the project root with "
        "PYTHONPATH set. That is the only reason the launcher exists, and it is worth one "
        "sentence on stage.", BODY))
    s.append(Paragraph(
        "<b>Case matters and differs between the modules:</b> cloud takes "
        "<font face='Courier'>greedy</font> in lower case, EV takes "
        "<font face='Courier'>Greedy</font> capitalised.", BODY))

    s.append(Paragraph("2. Setup, the evening before, on the presentation machine", H2))
    s.append(code_block([
        "# work from a copy, so a demo run does not leave your results dirty",
        'cp -R "/path/to/Master_Thesis_Metaheuristics" ~/demo',
        "cd ~/demo",
        "",
        "# run both twice: the first pass downloads packages and warms the",
        "# uv cache, the second pass is the real timing to plan around",
        "time uv run run.py cloud -a SA GA UMDA greedy -s 1",
        "time uv run run.py ev -a SA Greedy -s 1",
    ], accent=GREEN))
    s.append(Spacer(1, 5))
    s.append(Paragraph(
        "Write down what <font face='Courier'>time</font> reports on the second pass. Those "
        "two numbers are what the run sheet in section 5 should be built around. Measured "
        "on a Windows laptop the runs take 79 s and 93 s warm, against 100 s cold; on the "
        "Apple M3 Pro that produced the committed results, expect roughly 15 s and 25 s. "
        "Measure, do not assume.", BODY))
    s.append(Paragraph(
        "The copy is hygiene, not a safety rule. A run overwrites the results directory it "
        "writes to, so running in the real tree leaves it dirty and, if committed, puts "
        "1-seed numbers in a repository whose README says its results came from full runs. "
        "Nothing you project comes from those files, and "
        "<font face='Courier'>git checkout</font> undoes it in two seconds. One "
        "<font face='Courier'>cd</font> avoids the question entirely.", BODY))

    s.append(Paragraph("3. Machine and logistics", H2))
    s.append(Paragraph(
        "Use <b>one laptop for the whole demo</b>, the Mac that produced the committed "
        "results. Swapping laptops mid-demo costs 30 to 60 seconds of dead air out of 300 "
        "and is the most common way a two-person demo falls apart.", BODY))
    s.append(table(
        ["Item", "Do this", "Why"],
        [["Power", "Plug in, disable Low Power Mode",
          "macOS throttles hard on battery; this alone can turn 15 s into 60 s"],
         ["Background apps", "Quit Docker, Chrome, Slack",
          "The runs are single-threaded but memory and thermal pressure still bite"],
         ["Windows layout", "Terminal left half, image viewer right half, set before you walk in",
          "Never resize or rearrange anything live"],
         ["GIF playback", "Open the GIFs in a browser tab, not Preview.app",
          "Preview treats a GIF as a multi-page document and shows a still frame. "
          "Quick Look (spacebar) animates; verify on the actual machine"],
         ["Terminal font", "16 to 18 pt", "It is a lecture room, not your desk"],
         ["Fallback", "Screen-record the full 5 minutes the day before",
          "If the projector, laptop or network fails you play the recording and lose nothing"],
         ["Recovery tab", "A second terminal tab holding a completed run, scrolled to the summary",
          "Instant recovery if anything hangs on stage"],
         ["Windows only", "<font face='Courier'>export PYTHONIOENCODING=utf-8</font>",
          "EV main.py crashes with UnicodeEncodeError on the Wilcoxon header in cp1252. "
          "Not an issue on macOS"],
         ], [26 * mm, 56 * mm, W - 82 * mm], accent=ORANGE))

    s.append(Paragraph("4. Files to have open before you start", H2))
    s.append(code_block([
        "~/demo/Cloud_scheduling/figures/balanced/allocation_greedy_construction.gif",
        "~/demo/Cloud_scheduling/figures/balanced/allocation_sa_search.gif",
        "~/demo/Cloud_scheduling/results/balanced/run_manifest.yaml",
        "~/demo/report/graphics/sf75_instance_map.png",
        "~/demo/EV_routing/results/sf_75/figures/route_comparison_map.png",
        "~/demo/EV_routing/results/sf_75/summary.md",
    ], accent=GREEN))

    # ---------------------------------------------------------------- page 2
    s.append(CondPageBreak(130 * mm))
    s.append(Paragraph("5. The five minutes, minute by minute", H1))
    s.append(Paragraph(
        "Timings assume the Mac. On the Mac each run finishes before you finish the "
        "sentence that launched it, so the structure is <b>result first, explanation "
        "second</b>. Do not try to talk over the run to fill time; there is no time to "
        "fill. Christian takes cloud scheduling, Daniel takes EV routing, which also "
        "satisfies the equal-speaking-time requirement.", BODY))
    s.append(table(
        ["Time", "Who", "What happens", "What you say"],
        [["0:00", "C", "Paste the cloud command. Lands in about 15 s.",
          "\"Fifty tasks, ten servers, one seed, a hundred and fifty thousand objective "
          "evaluations.\""],
         ["0:30", "C", "Point at SA best = 1.8086, thesis table beside it.",
          "\"That is the same number to four decimals as the table in chapter 6. Seed 0 "
          "happens to be the best of our twenty seeds.\""],
         ["0:45", "C", "Greedy construction GIF (27 s), then SA search GIF (17 s).",
          "\"Each rack is a server, height is CPU capacity, colour is task priority. "
          "This is what those evaluations were actually doing.\""],
         ["1:30", "C", "One scroll of run_manifest.yaml.",
          "\"Every run writes a manifest next to its results: CLI arguments, calibrated "
          "constants, every hyperparameter. That is how any number in the thesis traces "
          "back to the run that produced it.\""],
         ["1:50", "-", "Handover.", "Agree the exact sentence in advance."],
         ["2:10", "D", "Paste the EV command. Lands in about 25 s.",
          "\"Seventy-five customers and thirty real charging stations in San Francisco, "
          "road distances from OSRM, elevations from SRTM.\""],
         ["2:40", "D", "Instance map, then route comparison map.",
          "\"Greedy goes 309 km and burns 111 kWh. SA goes 258 km on 78 kWh and pays "
          "$9.73 in charging instead of $24.10. Thirty percent less energy, and the "
          "charging bill drops by sixty percent.\""],
         ["3:50", "D", "summary.md, scrolled to the ranking.",
          "\"Same protocol as the cloud problem: fixed evaluation budget, frozen tuned "
          "parameters, twenty seeds in the thesis, Wilcoxon with Holm correction.\""],
         ["4:20", "C/D", "Results directory layout, 33 unit tests, README.",
          "\"Both modules follow the same protocol and both are reproducible from the "
          "repository.\""],
         ["4:40", "-", "Buffer.", "Stop talking. Do not fill it."],
         ], [13 * mm, 10 * mm, 52 * mm, W - 75 * mm]))

    s.append(Paragraph("6. Numbers you are allowed to quote", H2))
    s.append(Paragraph(
        "The live run uses <b>one seed</b>. The thesis reports <b>twenty</b>. For cloud "
        "these coincide; for EV they do not. Say \"one seed\" out loud on the EV half, "
        "otherwise a censor with the table open will catch the mismatch.", BODY))
    s.append(table(
        ["Quantity", "Live 1-seed run", "Thesis value", "How to phrase it"],
        [["Cloud SA", "1.8086", "1.8086 (best of 20)",
          "\"Identical. Seed 0 is our best seed.\""],
         ["Cloud greedy BFD", "2.0062", "2.0062", "\"Deterministic, so it is exact.\""],
         ["Cloud improvement", "+9.9 %", "+9.9 %", "\"Search beats construction by ten percent.\""],
         ["EV greedy", "3.5969", "3.5969", "\"Deterministic, exact match.\""],
         ["EV SA", "2.5044", "2.4649 best, 2.5583 mean",
          "\"One seed, so it sits between our twenty-seed best and mean.\""],
         ["EV improvement", "+30.4 %", "+31.0 %", "\"About thirty percent over the baseline.\""],
         ], [30 * mm, 26 * mm, 36 * mm, W - 92 * mm], accent=GREEN))

    # ---------------------------------------------------------------- page 3
    s.append(CondPageBreak(130 * mm))
    s.append(Paragraph("7. What actually happens when you press enter", H1))
    s.append(Paragraph(
        "Phase by phase, so you can narrate confidently and answer \"what is it doing "
        "right now\". Times are the Windows measurements; divide by roughly five for the "
        "Mac.", BODY))

    s.append(Paragraph("Cloud scheduling, approx. 79 s Windows / 15 s Mac", H2))
    s.append(table(
        ["Phase", "On screen", "Say this, and why it matters"],
        [["Instance", "50 tasks, 10 servers, 2256.7 % CPU demand against 4300 % capacity.",
          "The instance is oversubscribed enough that placement matters, but it is "
          "feasible. This frames the whole problem in one line."],
         ["Calibration<br/>(2 s)",
          "25/150 feasible samples. E_ref = 12572 W, L_ref = 29267 ms, lambda = 206.47.",
          "<b>The best technical moment of the cloud half.</b> Watts and milliseconds are "
          "not comparable, so the objective is normalised by references sampled from the "
          "instance itself, and the capacity penalty is set to 100x the worst feasible "
          "objective so no infeasible solution can ever beat a feasible one."],
         ["Focus mode", "BALANCED, w_energy = w_latency = 1.0.",
          "One switch in config.yaml moves this to eco or performance. The objective is "
          "configuration, not code."],
         ["SA diagnostic<br/>(16 s)",
          "F(X) = 1.8146, acceptance 30.55 %, 6 reheats, per-server task histogram "
          "(19, 8, 6, 5, 3, 2, 2, 2, 2, 1).",
          "The histogram is the most legible thing in the whole log. That skew is the "
          "consolidation-versus-congestion trade-off made visible. Note SA runs twice: "
          "this diagnostic, then the seeded comparison."],
         ["Multi-seed<br/>(50 s)", "One line per algorithm: SA, GA, UMDA, greedy.",
          "All three metaheuristics under an identical 150,000-evaluation budget. Equal "
          "budget is what makes the comparison fair."],
         ["Summary",
          "SA 1.81, GA 1.82, UMDA 1.82, greedy 2.01. Energy contributes 55 %, latency 45 %.",
          "SA wins, but the margin over GA and UMDA is under one percent, and with one "
          "seed you cannot claim significance. Say so before you are asked."],
         ["Outputs<br/>(10 s)", "4 figures, 3 CSVs, run_manifest.yaml, summary.md.",
          "Every run is self-documenting. This is the reproducibility argument."],
         ], [22 * mm, 60 * mm, W - 82 * mm]))

    s.append(Paragraph("EV routing, approx. 93 s Windows / 25 s Mac", H2))
    s.append(table(
        ["Phase", "On screen", "Say this, and why it matters"],
        [["Load", "Weights loaded from weights.json, multipliers all 1.0.",
          "Weights were calibrated in a separate, committed step and then frozen. The run "
          "does not tune itself, which is what makes it a controlled comparison."],
         ["SA diagnostic<br/>(35 s)",
          "Objective 2.5815, 273 km, 82.2 kWh, acceptance 14.9 %, 7 reheats.",
          "Acceptance is 14.9 % here against 30.6 % in the cloud problem. The EV landscape "
          "is far more constrained, because battery feasibility rejects most moves."],
         ["Greedy<br/>(0.00 s)",
          "3.5969, 309.2 km, 111.3 kWh, 1.15 h charging, $24.10.",
          "Nearest-neighbour with a charging repair. Instant, feasible, and clearly poor. "
          "This is the number everything else is measured against."],
         ["Comparison<br/>(42 s)", "SA seed 0 lands on 2.5044.",
          "Same 150,000-evaluation budget as the cloud problem. One protocol, two problems."],
         ["Interpretation",
          "+30.4 % over greedy. SA best run: 258.5 km, 77.7 kWh, $9.73.",
          "<b>Quote the physical numbers, not the objective value.</b> \"Thirty percent "
          "less energy and a sixty percent smaller charging bill\" lands with a censor. "
          "\"2.50 versus 3.60\" does not."],
         ["Outputs<br/>(10 s)", "5 figures, 3 CSVs, manifest, summary.md.",
          "Identical output contract to the cloud module, written independently."],
         ], [22 * mm, 60 * mm, W - 82 * mm]))

    # ---------------------------------------------------------------- page 4
    s.append(CondPageBreak(110 * mm))
    s.append(Paragraph("8. Five things on screen that can bite you", H1))
    s.append(Paragraph(
        "All five are real, all five were observed in a rehearsal run. None is a bug in "
        "the science, but each one looks bad on a projector if it surprises you.", BODY))

    s.append(KeepTogether([callout(
        "1. The Wilcoxon table at one seed says \"no sig. difference\", p = 1.0000.",
        "With n = 1 the signed-rank test has no power at all, so W = 0 and p = 1. "
        "Projected on a wall, \"no significant difference between Greedy and SA\" reads as "
        "your method failing. <b>Say the sentence before it appears:</b> \"one seed, so "
        "the test is a placeholder here; the thesis runs twenty and the difference is "
        "significant after Holm correction.\" Alternatively run the EV demo with "
        "<font face='Courier'>-s 3</font>, which costs about 30 extra seconds on the Mac "
        "and produces a table that does not say that."), Spacer(1, 6)]))

    s.append(KeepTogether([callout(
        "2. The printed LaTeX table is captioned \"(10 seeds, mean +/- std)\" whatever you ran.",
        "The caption default is hard-coded in EV_routing/tools/statistics.py line 196 and "
        "does not follow the actual seed count, so on a 1-seed run it contradicts the "
        "\"1 seeds\" header two lines above it. Do not leave that block on screen. If "
        "asked, it is a cosmetic default in a convenience helper that writes a table for "
        "pasting into the report, and the reported tables were produced from 20-seed "
        "runs.", accent=ORANGE), Spacer(1, 6)]))

    s.append(KeepTogether([callout(
        "3. Two different SA numbers appear in the EV run: 2.5815, then 2.5044.",
        "The first is the diagnostic call at EV_routing/main.py line 1288, which is not "
        "given a seed. The second is seed 0 of the controlled comparison. Know this before "
        "somebody asks why SA produced two answers. The seeded one is the number that goes "
        "in the results.", accent=ORANGE), Spacer(1, 6)]))

    s.append(KeepTogether([callout(
        "4. The EV run ends by dumping both full routes.",
        "Eighty-five node IDs each, filling the screen, and it is the last thing printed. "
        "The summary table you want to point at is scrolled well above it. Either scroll "
        "back up before you start talking, or plan to finish on summary.md instead.",
        accent=ORANGE), Spacer(1, 6)]))

    s.append(KeepTogether([callout(
        "5. A matplotlib UserWarning prints near the top of the EV run.",
        "set_ticklabels() from tools/plot.py line 350. Harmless, but it is yellow and it "
        "is the first thing on the screen. Ignore it; if asked, it is a tick-locator "
        "warning from a figure helper.", accent=ORANGE)]))

    s.append(CondPageBreak(95 * mm))
    s.append(Paragraph("9. Why the demo is built this way", H1))
    s.append(table(
        ["Choice", "Reason"],
        [["One seed, not twenty",
          "Twenty seeds is 3.5 minutes for cloud and 39 minutes for EV. One seed is the "
          "same code, the same budget and the same protocol, finishing inside the time "
          "available. The full runs are already committed, so the demo shows the machinery "
          "and the repository shows the evidence."],
         ["Real entry point, not a demo script",
          "The credibility of a software demo is the examiner seeing the documented "
          "command invoked. A wrapper would hide exactly the thing worth witnessing, and "
          "would be new unrehearsed code introduced days before the defence into the one "
          "part of the event with live failure risk."],
         ["SA, GA, UMDA for cloud but only SA for EV",
          "Cloud has three metaheuristics at 15 s each on the Mac, so all three fit. In EV, "
          "GA and ACO cost 43 s and 54 s per seed even on the M3 and would take the whole "
          "five minutes on their own. SA is the winner in both problems, so it is the one "
          "to show."],
         ["Animations pre-rendered, not generated live",
          "Rendering the SA GIF takes about a minute even at reduced budget. It is "
          "generated by <font face='Courier'>visualize.py --animate sa</font> from the "
          "same code path as the results, so say the command out loud rather than pretend "
          "it is live."],
         ["Sandbox copy",
          "A run overwrites the results directory it writes to. The committed results back "
          "the tables in the thesis. Those two facts are why the demo runs in ~/demo."],
         ["Physical units in the narration",
          "Kilometres, kilowatt-hours and dollars are immediately meaningful. A normalised "
          "objective value is not, and inviting a question about how F(X) is scaled in the "
          "middle of a five-minute demo is a poor trade."],
         ], [45 * mm, W - 45 * mm], accent=GREEN))

    s.append(Spacer(1, 8))
    s.append(Paragraph(
        "<i>Generated by make_demo_guide.py. Runtimes measured 19 August 2026: Windows 11 "
        "laptop for the absolute figures, per-algorithm Apple M3 Pro times taken from the "
        "committed results_summary.csv. Re-measure on the presentation machine.</i>", SMALL))

    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=22 * mm,
        title="Software demo run sheet - MSc defence 28 August 2026",
        author="Christian Wu and Daniel Diamant",
        subject="Demo guide for the thesis defence software demonstration",
    )
    frame = Frame(MARGIN, 22 * mm, CONTENT_W, PAGE_H - MARGIN - 22 * mm, id="f")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_chrome)])
    doc.build(s)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
