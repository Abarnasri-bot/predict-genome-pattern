from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import sqlite3, csv, io, json, random
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "dreamverse.db"
UPLOAD_PATH = DATA_DIR / "uploaded_dataset.csv"

app = Flask(__name__)

FEATURES = ["A_count", "T_count", "G_count", "C_count", "Length", "GC_percent"]
EXAMPLE_ROWS = [
    {"Sequence ID": "S1", "DNA Sequence": "ATGCGATC", "Group": "A"},
    {"Sequence ID": "S2", "DNA Sequence": "ATGCGTAC", "Group": "A"},
    {"Sequence ID": "S3", "DNA Sequence": "GCGCGTAT", "Group": "B"},
    {"Sequence ID": "S4", "DNA Sequence": "GCGCGCGC", "Group": "B"},
]
MODEL_CACHE = {"model": None, "source": None, "accuracy": None, "evaluation": None, "rows": None}


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence TEXT NOT NULL,
            group_result TEXT NOT NULL,
            features_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )""")


def clean_sequence(seq):
    seq = "".join(str(seq).upper().split())
    if not seq:
        raise ValueError("Please enter a DNA sequence.")
    invalid = sorted(set(seq) - set("ATGC"))
    if invalid:
        raise ValueError("Only A, T, G and C are accepted. Invalid character(s): " + ", ".join(invalid))
    return seq


def extract_features(seq):
    seq = clean_sequence(seq)
    n = len(seq)
    a, t, g, c = (seq.count(x) for x in "ATGC")
    return {
        "A_count": a, "T_count": t, "G_count": g, "C_count": c,
        "Length": n, "GC_percent": round(((g + c) / n) * 100, 2)
    }


def make_demo_rows():
    # A transparent synthetic teaching set: Group A sequences are AT-rich;
    # Group B sequences are GC-rich. This is NOT biological ground truth.
    rng = random.Random(2606)
    rows = list(EXAMPLE_ROWS)
    for i in range(120):
        group = "A" if i % 2 == 0 else "B"
        weights = [0.35, 0.35, 0.15, 0.15] if group == "A" else [0.15, 0.15, 0.35, 0.35]
        seq = "".join(rng.choices(["A", "T", "G", "C"], weights=weights, k=rng.randint(12, 45)))
        rows.append({"Sequence ID": f"DEMO{i+1}", "DNA Sequence": seq, "Group": group})
    return pd.DataFrame(rows)


def load_training_data():
    if UPLOAD_PATH.exists():
        df = pd.read_csv(UPLOAD_PATH)
        cols = {str(c).strip().lower(): c for c in df.columns}
        required = ["sequence id", "dna sequence", "group"]
        missing = [x for x in required if x not in cols]
        if missing:
            raise ValueError("CSV must contain columns: Sequence ID, DNA Sequence, Group.")
        df = df.rename(columns={
            cols["sequence id"]: "Sequence ID",
            cols["dna sequence"]: "DNA Sequence",
            cols["group"]: "Group"
        })
        source = "Uploaded assignment dataset"
    else:
        df = make_demo_rows()
        source = "Built-in synthetic demo dataset"
    df = df.dropna(subset=["DNA Sequence", "Group"]).copy()
    df["DNA Sequence"] = df["DNA Sequence"].apply(clean_sequence)
    df["Group"] = df["Group"].astype(str).str.strip()
    if df["Group"].nunique() < 2:
        raise ValueError("Training data must contain at least two groups.")
    return df, source


def train_model(force=False):
    if MODEL_CACHE["model"] is not None and not force:
        return MODEL_CACHE
    df, source = load_training_data()
    feats = pd.DataFrame([extract_features(s) for s in df["DNA Sequence"]])
    X, y = feats[FEATURES], df["Group"]
    counts = y.value_counts()
    evaluation = None
    accuracy = None
    model = DecisionTreeClassifier(max_depth=5, random_state=42)
    # Hold-out test evaluation is only attempted when enough examples exist.
    if len(df) >= 12 and counts.min() >= 3:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )
        evaluation_model = DecisionTreeClassifier(max_depth=5, random_state=42)
        evaluation_model.fit(X_train, y_train)
        pred = evaluation_model.predict(X_test)
        accuracy = round(accuracy_score(y_test, pred) * 100, 2)
        evaluation = {
            "accuracy": accuracy,
            "test_count": int(len(y_test)),
            "report": classification_report(y_test, pred, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, pred).tolist()
        }
    model.fit(X, y)
    MODEL_CACHE.update(model=model, source=source, accuracy=accuracy,
                       evaluation=evaluation, rows=df)
    return MODEL_CACHE


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/status")
def status():
    try:
        m = train_model()
        return jsonify({
            "ok": True, "source": m["source"], "rows": len(m["rows"]),
            "accuracy": m["accuracy"],
            "accuracy_note": ("Held-out test accuracy" if m["accuracy"] is not None
                              else "Not reported: dataset too small for reliable hold-out evaluation")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/analyze")
def analyze():
    body = request.get_json(force=True)
    try:
        seq = clean_sequence(body.get("sequence", ""))
        feats = extract_features(seq)
        m = train_model()
        X = pd.DataFrame([feats])[FEATURES]
        prediction = str(m["model"].predict(X)[0])
        probs = m["model"].predict_proba(X)[0]
        confidence = round(float(max(probs)) * 100, 1)
        with db() as con:
            con.execute(
                "INSERT INTO predictions(sequence, group_result, features_json, created_at) VALUES(?,?,?,?)",
                (seq, prediction, json.dumps(feats), datetime.now().isoformat(timespec="seconds"))
            )
        return jsonify({
            "sequence": seq, "features": feats, "prediction": prediction,
            "confidence": confidence, "model_source": m["source"],
            "accuracy": m["accuracy"],
            "warning": "Demo predictions are educational only. Use your real labelled class dataset for assignment results."
                       if m["source"].startswith("Built-in") else
                       "Predictions depend on the patterns represented in the uploaded dataset."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/upload")
def upload():
    global MODEL_CACHE
    file = request.files.get("dataset")
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Please choose a CSV dataset file."}), 400
    try:
        content = file.read()
        df = pd.read_csv(io.BytesIO(content))
        cols = {str(c).strip().lower() for c in df.columns}
        if not {"sequence id", "dna sequence", "group"}.issubset(cols):
            return jsonify({"error": "CSV needs columns: Sequence ID, DNA Sequence, Group."}), 400
        # Validate rows before saving.
        seq_col = next(c for c in df.columns if str(c).strip().lower() == "dna sequence")
        for seq in df[seq_col].dropna():
            clean_sequence(seq)
        UPLOAD_PATH.write_bytes(content)
        MODEL_CACHE.update(model=None, source=None, accuracy=None, evaluation=None, rows=None)
        m = train_model(force=True)
        return jsonify({"message": "Dataset uploaded and model retrained.", "source": m["source"],
                        "rows": len(m["rows"]), "accuracy": m["accuracy"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/report")
def report():
    try:
        m = train_model()
        df = m["rows"].copy()
        feature_rows = pd.DataFrame([extract_features(s) for s in df["DNA Sequence"]])
        out = pd.concat([df[["Sequence ID", "DNA Sequence", "Group"]].reset_index(drop=True),
                         feature_rows], axis=1)
        stream = io.StringIO()
        out.to_csv(stream, index=False)
        mem = io.BytesIO(stream.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="dreamverse_feature_table.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/history")
def history():
    with db() as con:
        rows = con.execute("SELECT sequence, group_result, created_at FROM predictions ORDER BY id DESC LIMIT 12").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/score")
def score():
    body = request.get_json(force=True)
    player = str(body.get("player", "Dream Explorer"))[:40]
    score_value = max(0, min(9999, int(body.get("score", 0))))
    with db() as con:
        con.execute("INSERT INTO game_scores(player, score, created_at) VALUES(?,?,?)",
                    (player, score_value, datetime.now().isoformat(timespec="seconds")))
    return jsonify({"saved": True})


@app.get("/api/leaderboard")
def leaderboard():
    with db() as con:
        rows = con.execute("SELECT player, MAX(score) AS score FROM game_scores GROUP BY player ORDER BY score DESC LIMIT 5").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/examples")
def examples():
    return jsonify(EXAMPLE_ROWS)


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
