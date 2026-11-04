# DREAMVERSE — The Genome of Dreams

A beginner-friendly full-stack website for the Introduction to Computational Biology assignment.

## Included features

### Assignment 2 requirements
- DNA sequence input
- Feature extraction: A, T, G, C counts, sequence length and GC%
- Decision Tree classifier
- Unknown-sequence prediction (default: `ATGCGCGATC`)
- Held-out test accuracy when enough labelled examples are available
- Feature table CSV download
- Upload the actual assignment CSV and retrain the model

### Our extra ideas
- Dark dreamcore / weirdcore visual design with colourful glow effects
- Three dream-world cards
- DNA fragment collection mini-game
- 3D-inspired animated planet hero scene
- Prediction history stored in SQLite
- Mini-game leaderboard stored in SQLite
- Responsive design for desktop and mobile

## Run on Windows

1. Install Python 3.10 or newer.
2. Extract this ZIP folder.
3. Open the extracted `DREAMVERSE_ICB` folder.
4. Click the address bar in File Explorer, type `cmd`, and press Enter.
5. Run:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

6. Open this address in Chrome:

`http://127.0.0.1:5000`

Keep the terminal window open while using the website.

## Use your assignment dataset

Prepare a CSV with these exact column names:

```csv
Sequence ID,DNA Sequence,Group
S1,ATGCGATC,A
S2,ATGCGTAC,A
S3,GCGCGTAT,B
S4,GCGCGCGC,B
```

The four rows above are only the examples printed in the assignment sheet. Replace/add the full dataset supplied by your instructor. In Genome Lab, choose the CSV and click **UPLOAD & TRAIN MODEL**. The app validates it, saves it locally, and retrains the classifier.

## Try any new sequence

In Genome Lab, paste any sequence containing only A, T, G and C, for example:

`ATGCGCGATCGATCGGCTA`

Click **ANALYZE SEQUENCE**. You can repeat this for as many sequences as you like.

## Important scientific note

If no instructor dataset has been uploaded, the app uses a built-in **synthetic teaching dataset**. It creates example Group A sequences that are more AT-rich and Group B sequences that are more GC-rich. This is only a demonstration pattern so the site works immediately; it is not a validated biological rule and its predictions are not scientific conclusions.

The four assignment examples alone are too small to provide a meaningful generalization estimate. The app therefore avoids reporting a held-out accuracy for very small datasets. For your final assignment report, upload the actual labelled dataset and use its measured results. State the dataset source and limitations honestly.

## Files

- `app.py` — Flask backend, feature extraction, model training, prediction API, SQLite database
- `templates/index.html` — website structure
- `static/css/style.css` — dreamcore styling
- `static/js/app.js` — interactions, game, API calls
- `data/` — uploaded dataset and SQLite database are created here when you run the app

## Assignment discussion points you can use

- Features: nucleotide counts and GC percentage summarize sequence composition; sequence length provides context.
- Model: a Decision Tree learns rules from labelled examples.
- Generalization: a sequence unlike the training data may be classified incorrectly.
- Limitations: small or biased datasets, short-sequence composition features, and lack of biological context can reduce reliability.
- Application: sequence classification can support exploratory genomic data analysis, such as grouping sequences by known labels before deeper investigation.
