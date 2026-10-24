from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-before-deployment"
DB = Path(__file__).with_name("capstone57.db")

TOOLS = ["ChatGPT", "Google Gemini", "Claude", "Microsoft Copilot"]
CRITERIA = [
    ("accuracy", "Accuracy"), ("completeness", "Completeness"),
    ("instruction_following", "Instruction following"), ("clarity", "Clarity"),
    ("modality_understanding", "Modality understanding"),
    ("source_verification", "Source verification")
]
TASKS = [
("T01","Diagram reading","Image","Describe components and arrow relationships. Do not guess unreadable labels."),
("T02","Chart interpretation","Image","Identify highest and lowest values, compare categories and describe a trend."),
("T03","Image description","Image","Describe only visible details; separate observation from inference."),
("T04","Visual error detection","Image","Find inconsistencies and cite visual evidence."),
("T05","PDF summary","Document","Summarize the document in 150 words, preserving the main claim, three points and one limitation."),
("T06","Document Q&A","Document","Answer using only the document and give page/section references; say if absent."),
("T07","Table extraction","Document","Convert a table to Markdown without changing labels, values or units."),
("T08","Compare passages","Document","List shared points and differences with supporting references."),
("T09","Factual verification","Text + sources","Label claims Supported, Contradicted or Not verifiable from the supplied sources."),
("T10","Audio transcription","Audio","Transcribe verbatim; preserve names, numbers and negation; mark unclear words."),
("T11","Audio study notes","Audio","Create five notes and three revision questions using only the supplied audio/transcript."),
("T12","Concept explanation","Text","Explain a concept for a first-year student using an analogy and its limitations."),
("T13","Quiz generation","Document","Create five multiple-choice questions from the lesson with an answer key and references."),
("T14","Dated information check","Web/source","State what a dated source confirms and what remains uncertain."),
("T15","Error correction","Any","Check statements against a source, correct errors and flag unverifiable claims.")
]
PROMPTS = [
("Image analysis","Analyze the image. List readable labels, explain visible relationships, separate observations from inferences, and mark uncertainty."),
("Chart reading","Report the chart title, axes, units, highest and lowest values, and one trend. Do not silently guess unclear values."),
("PDF summary","Summarize the PDF in 150 words with the main claim, three supporting points, and one limitation. Use only the PDF."),
("Document Q&A","Answer only from the supplied document. Give page/section evidence or say 'Not stated in the document.'"),
("Audio transcription","Transcribe verbatim, preserving names, numbers, technical terms and negation. Use [unclear] rather than guessing."),
("Fact-checking","Label each claim Supported, Contradicted, or Not verifiable from these sources. Identify evidence; do not invent citations."),
("Hallucination audit","Compare each claim with the source and list evidence, status, correction and confidence."),
("Quiz generation","Create five multiple-choice questions from the supplied lesson, with one correct answer, answer key and source references.")
]
QUIZ = [
("What is a hallucination?",["A supported claim","An unsupported or fabricated claim","A source link","A score formula"],1,"A hallucination is not supported by the input or reliable evidence."),
("Why use the same prompt across tools?",["To reduce testing bias","To guarantee identical answers","To avoid evidence","To increase file size"],0,"Standardized prompts make comparisons fairer."),
("What if a feature is unavailable?",["Score accuracy zero","Invent an output","Record unavailable","Hide the result"],2,"Availability and accuracy are different."),
("Why save raw outputs?",["For evidence and reproducibility","To avoid checking","To improve scores","To hide mistakes"],0,"Raw outputs support transparent review."),
("How should a PDF summary be checked?",["Style only","Against the PDF","Assume correct","Skip footnotes"],1,"The source document is the reference."),
("Which audio details need checking?",["Names and numbers","Only punctuation","Page colour","Font size"],0,"Transcription mistakes can change meaning."),
("What does a score of 5 mean?",["Unavailable","Excellent for the criterion","Not tested","Always false"],1,"Five means excellent performance in this rubric."),
("Why record a test date?",["Tools never change","Features and limits change","To skip citations","To hide the model"],1,"Product capabilities can change over time."),
("What should you avoid uploading?",["Public material","Approved worksheets","Private/confidential files without permission","Synthetic samples"],2,"Minimize privacy risks."),
("When can you name the best tool?",["Before testing","From popularity","After comparing recorded results","By guessing"],2,"Conclusions must follow evidence.")
]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS results (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, tool TEXT, tested_at TEXT,
          model_version TEXT, modality TEXT, status TEXT, prompt TEXT, output_summary TEXT,
          evidence_url TEXT, accuracy REAL, completeness REAL, instruction_following REAL,
          clarity REAL, modality_understanding REAL, source_verification REAL, error_notes TEXT)""")
        c.commit()

@app.route("/")
def home():
    with db() as c:
        total = c.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        summaries = c.execute("""SELECT tool, COUNT(*) runs,
          SUM(CASE WHEN status!='Tested' THEN 1 ELSE 0 END) unavailable,
          ROUND(AVG(CASE WHEN status='Tested' AND accuracy IS NOT NULL
          THEN (accuracy+completeness+instruction_following+clarity+modality_understanding+source_verification)/30.0*100 END),2) avg
          FROM results GROUP BY tool ORDER BY avg DESC""").fetchall()
    return render_template("home.html", total=total, summaries=summaries)

@app.route("/tasks")
def tasks():
    return render_template("tasks.html", tasks=TASKS)

@app.route("/record", methods=["GET","POST"])
def record():
    if request.method == "POST":
        task_id = request.form.get("task_id","")
        tool = request.form.get("tool","")
        status = request.form.get("status","Tested")
        task = next((t for t in TASKS if t[0] == task_id), None)
        if not task or tool not in TOOLS:
            flash("Choose a valid task and tool.", "error")
            return redirect(url_for("record"))
        scores = {}
        if status == "Tested":
            try:
                for key, label in CRITERIA:
                    value = float(request.form.get(key,""))
                    if not 0 <= value <= 5: raise ValueError
                    scores[key] = value
            except (ValueError, TypeError):
                flash("Enter all six scores from 0 to 5 for a tested task.", "error")
                return redirect(url_for("record"))
        else:
            scores = {key: None for key, label in CRITERIA}
        vals = [
            task_id, tool, request.form.get("tested_at") or datetime.now().strftime("%Y-%m-%d %H:%M"),
            request.form.get("model_version",""), request.form.get("modality",task[2]), status,
            request.form.get("prompt",task[3]), request.form.get("output_summary",""),
            request.form.get("evidence_url",""), scores["accuracy"], scores["completeness"],
            scores["instruction_following"], scores["clarity"], scores["modality_understanding"],
            scores["source_verification"], request.form.get("error_notes","")
        ]
        with db() as c:
            c.execute("""INSERT INTO results(task_id,tool,tested_at,model_version,modality,status,prompt,
              output_summary,evidence_url,accuracy,completeness,instruction_following,clarity,
              modality_understanding,source_verification,error_notes)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
            c.commit()
        flash("Test record saved.", "success")
        return redirect(url_for("results"))
    task_id = request.args.get("task_id", "T01")
    selected = next((t for t in TASKS if t[0] == task_id), TASKS[0])
    return render_template("record.html", tasks=TASKS, tools=TOOLS, criteria=CRITERIA,
                           selected=selected, now=datetime.now().strftime("%Y-%m-%dT%H:%M"))

@app.route("/results")
def results():
    with db() as c:
        rows = c.execute("""SELECT *, CASE WHEN status='Tested' AND accuracy IS NOT NULL
          THEN ROUND((accuracy+completeness+instruction_following+clarity+modality_understanding+source_verification)/30.0*100,2)
          ELSE NULL END pct FROM results ORDER BY id DESC""").fetchall()
        summaries = c.execute("""SELECT tool, COUNT(*) runs,
          SUM(CASE WHEN status!='Tested' THEN 1 ELSE 0 END) unavailable,
          ROUND(AVG(CASE WHEN status='Tested' AND accuracy IS NOT NULL
          THEN (accuracy+completeness+instruction_following+clarity+modality_understanding+source_verification)/30.0*100 END),2) avg
          FROM results GROUP BY tool ORDER BY avg DESC""").fetchall()
    return render_template("results.html", rows=rows, summaries=summaries)

@app.route("/prompts")
def prompts():
    return render_template("prompts.html", prompts=PROMPTS)

@app.route("/checklist")
def checklist():
    items = ["Correctly identifies the task and modality","Reads labels, values and units accurately",
      "Preserves meaning in summaries","Includes important caveats","Separates facts from inferences",
      "Does not invent details","Provides relevant source references","Preserves names/numbers in audio",
      "States uncertainty for unreadable content","Follows requested format","Protects private information",
      "Checked against a trusted reference"]
    return render_template("checklist.html", items=items)

@app.route("/quiz", methods=["GET","POST"])
def quiz():
    if request.method == "POST":
        score = sum(1 for i,q in enumerate(QUIZ) if request.form.get(f"q{i}") == str(q[2]))
        return render_template("quiz.html", quiz=QUIZ, score=score, submitted=True)
    return render_template("quiz.html", quiz=QUIZ, submitted=False, score=None)

@app.route("/about")
def about():
    return render_template("about.html")

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
