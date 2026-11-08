# TB Susceptibility Lab

A small web workspace for exploring the bundled CRyPTIC demo dataset and running an experimental cross-validated baseline for drug susceptibility prediction.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL Streamlit prints in the terminal. The included `data/` folder contains sample labels and k-mer feature matrices for 13 drugs, plus the MIC concordance reference.

## Pages

- **Overview** — sample data summary and phenotype counts by drug.
- **Data explorer** — filter isolate records and inspect MIC and binary phenotype distributions.
- **Model lab** — run a five-fold stratified Random Forest regression baseline, view metrics and out-of-fold predictions, and download a CSV.

The baseline uses numeric `LOG2MIC_NEW` labels, selects the top 3% of k-mer features separately within each training fold, and evaluates held-out fold predictions. It is an exploratory demonstration, not a validated clinical model. The research source scripts and their outputs are retained in the original `Downloads/DRTB` folder; this app uses an independent interface and a compact copy of the mock data.

## Field and metric guide

- **MIC** is the laboratory's minimum inhibitory concentration measurement. A `<` or `>` prefix means the result is bounded by the tested assay range rather than an exact value.
- **Log₂ MIC** is the base-2 logarithm of the numeric MIC target. One unit corresponds to a two-fold change in MIC.
- **Susceptible / Resistant** are the source dataset's binary labels. **Unknown / unclassified** corresponds to its `U` label; **Not recorded** means a label is missing.
- **Isolate ID** identifies the sample row. **Study site code** identifies the contributing study site. **Data split** marks rows as assigned to `Train` or held out as `Test` in the source example. **Bacterial lineage** describes broad genetic ancestry.
- **Mean absolute error (MAE)** is the average absolute distance between predicted and observed log₂ MIC; lower is closer. **R²** compares prediction error with predicting the average observed value: 1 is a perfect fit, 0 matches that simple reference, and a negative score is worse.
- **Five-fold validation** divides the sample into five parts, trains on four and predicts the held-out part, repeating until every isolate has an out-of-fold prediction. The app stratifies folds by the available binary labels.

All counts, scores and predictions describe the small bundled research demo. They are not clinical interpretations or treatment recommendations.
