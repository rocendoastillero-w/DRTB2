from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DRUGS = {
    "AMI": "Amikacin", "BDQ": "Bedaquiline", "CFZ": "Clofazimine",
    "DLM": "Delamanid", "EMB": "Ethambutol", "ETH": "Ethionamide",
    "INH": "Isoniazid", "KAN": "Kanamycin", "LEV": "Levofloxacin",
    "LZD": "Linezolid", "MXF": "Moxifloxacin", "RFB": "Rifabutin", "RIF": "Rifampicin",
}
CATALOG_PATH = DATA / "drug_catalog.json"

def get_drug_catalog():
    """Load the active catalog, discovering bundled drug pairs on first run."""
    discovered = {}
    for label_path in sorted(DATA.glob("*.0050.labels.csv")):
        code = label_path.name.split(".", 1)[0].upper()
        feature_path = DATA / f"{code}.0050.features.h5"
        if feature_path.exists():
            discovered[code] = DRUGS.get(code, code)
    if not CATALOG_PATH.exists():
        CATALOG_PATH.write_text(json.dumps(discovered, indent=2), encoding="utf-8")
        return discovered
    try:
        saved = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        return {code: name for code, name in saved.items()
                if (DATA / f"{code}.0050.labels.csv").exists()
                and (DATA / f"{code}.0050.features.h5").exists()}
    except (OSError, json.JSONDecodeError):
        return discovered

def save_drug_catalog(catalog):
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
PHENOTYPE_NAMES = {"S": "Susceptible", "R": "Resistant", "U": "Unknown / unclassified"}
FIELD_NAMES = {
    "UNIQUEID": "Isolate ID", "SITEID": "Study site code", "SPLIT": "Data split",
    "MIC_NEW": "MIC measurement", "LOG2MIC_NEW": "Log₂ MIC", "BINARY_PHENOTYPE": "Susceptibility",
    "LINEAGE_NAME": "Bacterial lineage", "PRED_LOG2MIC": "Predicted log₂ MIC",
}
st.set_page_config(page_title="TB Susceptibility Lab", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{--ink:#263238;--muted:#59666c;--line:#e1e5e8;--paper:#eef1f4;--teal:#587f82;--lime:#d9e1e5}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--paper)}
[data-testid="stAppViewContainer"]{color:#172b35}
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"]{color:#334b52}
[data-testid="stSidebar"]{background:#eef1f4;color:#263238;border-right:1px solid #dfe4e8}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#34434a!important;font-size:14px!important;line-height:1.5!important}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] span{color:#5e5a5a!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#5e5a5a!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{color:#263238!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:#263238!important}
[data-testid="stDataFrame"]{color:#172b35!important}
[data-testid="stDataFrame"] *{color:#172b35!important}
[data-testid="stDataFrame"] [data-testid="stDataFrameGlideDataEditor"]{background:#5e5a5a!important}
[data-testid="stDataFrame"] canvas{background:#d9d2d2 !important}
[data-testid="stDataFrame"] .stDataFrameGlideDataEditor{
  --gdg-bg-cell:#eef1f4!important;
  --gdg-bg-cell-medium:#eef1f4!important;
  --gdg-bg-header:#e3e8ec!important;
  --gdg-bg-header-hovered:#d9e0e5!important;
  --gdg-bg-header-has-focus:#d9e0e5!important;
  --gdg-bg-group-header:#e3e8ec!important;
  --gdg-bg-group-header-hovered:#d9e0e5!important;
  --gdg-text-dark:#172b35!important;
  --gdg-text-medium:#34434a!important;
  --gdg-text-light:#526169!important;
  --gdg-text-header:#34434a!important;
  --gdg-text-group-header:#34434a!important;
  --gdg-text-header-selected:#172b35!important;
  --gdg-bg-icon-header:#65747a!important;
  --gdg-fg-icon-header:#34434a!important;
  --gdg-bg-bubble:#e3e8ec!important;
  --gdg-bg-bubble-selected:#d9e0e5!important;
  --gdg-border-color:#dce2e6!important;
  --gdg-horizontal-border-color:#e5e9ec!important;
  --gdg-accent-color:#526a70!important;
  background:#eef1f4!important;
}
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"]{background:#eef1f4!important;border:1px solid #dce2e6!important}
[data-testid="stTable"]{background:#ffffff!important;color:#172b35!important}
[data-testid="stTable"] th,[data-testid="stTable"] td{background:#ffffff!important;color:#172b35!important}
.plain-table{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border:1px solid #d7dde2;border-radius:12px;background:#fff;color:#263238;font-size:13px}
.plain-table th{background:#e5e9ed;color:#263238;text-align:left;font-weight:700;padding:11px 13px;border-bottom:1px solid #cfd6dc;position:sticky;top:0}
.plain-table td{padding:10px 13px;color:#263238;border-bottom:1px solid #e1e5e8}
.plain-table tbody tr:nth-child(odd){background:#fff}
.plain-table tbody tr:nth-child(even){background:#f0f2f4}
.plain-table tbody tr:last-child td{border-bottom:0}
.table-wrap{width:100%;max-height:360px;overflow:auto;border-radius:12px;box-shadow:3px 3px 8px #d9dee3,-3px -3px 8px #fff}
.stTextInput input{color:#172b35!important;background:#fff!important}
.stTextInput input::placeholder{color:#65797e!important;opacity:1}
.stSelectbox [data-baseweb="select"]>div{background:#fff!important}
.stSelectbox [data-baseweb="select"] *{color:#172b35!important}
.stExpander summary p{color:#172b35!important}
.stButton button,.stDownloadButton button{background:#ffffff!important;color:#172b35!important;border:1px solid #cbd3d8!important;box-shadow:3px 3px 8px #d9dee3,-3px -3px 8px #fff!important;transition:background-color .15s ease,color .15s ease,border-color .15s ease}
.stButton button:hover,.stDownloadButton button:hover{background:#111820!important;color:#ffffff!important;border-color:#111820!important}
.stButton button:active,.stDownloadButton button:active{background:#252d33!important;color:#ffffff!important}
.hero{background:#f7f8fa;border:1px solid #fff;border-radius:20px;padding:34px 38px;color:#263238;margin:4px 0 22px;position:relative;overflow:hidden;box-shadow:8px 8px 18px #d8dde2,-8px -8px 18px #fff}
.hero:after{content:'◉';position:absolute;right:42px;top:-55px;font-size:230px;color:#dce2e7;opacity:.65}
.eyebrow{font:500 11px 'DM Mono';letter-spacing:2px;text-transform:uppercase;color:#587f82}
.hero h1{font-size:37px;line-height:1.12;letter-spacing:-1.4px;margin:12px 0 8px;color:#263238;max-width:670px}
.hero p{color:#526169;max-width:620px;margin:0;font-size:15px}
.metric{background:#f7f8fa;border:1px solid #fff;border-radius:15px;padding:18px 20px;min-height:112px;box-shadow:5px 5px 12px #d8dde2,-5px -5px 12px #fff}
.metric-label{font:11px 'DM Mono';letter-spacing:1px;text-transform:uppercase;color:#52676c}
.metric-value{font-size:29px;font-weight:700;letter-spacing:-1px;margin:8px 0 1px;color:var(--ink)}
.metric-note{font-size:12px;color:#52676c}
.section{font-size:21px;font-weight:700;letter-spacing:-.5px;margin:22px 0 4px}
.subtle{font-size:13px;color:#52676c;margin:0 0 14px}
.note{background:#f7f8fa;border:1px solid #fff;box-shadow:4px 4px 10px #d8dde2,-4px -4px 10px #fff;padding:12px 15px;border-radius:12px;color:#34434a;font-size:13px}
.stDownloadButton button,.stFileUploader section{border-radius:12px!important}
div[data-testid="stTabs"] button{font-weight:600}
.stButton>button[kind="primary"]{background:#087e79;border-color:#087e79}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_labels(drug):
    path = DATA / f"{drug}.0050.labels.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_features(drug):
    return pd.read_hdf(DATA / f"{drug}.0050.features.h5")

def card(label, value, note):
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

def show_table(frame, max_rows=None):
    """Render a simple HTML table to avoid the blank interactive grid canvas."""
    view=frame.head(max_rows) if max_rows else frame
    html=view.to_html(index=False,escape=True,border=0,classes="plain-table")
    st.markdown(f'<div class="table-wrap">{html}</div>',unsafe_allow_html=True)

def render_overview():
    st.markdown('<div class="hero"><div class="eyebrow">Research workspace · CRyPTIC demo</div><h1>Drug resistance, seen through the genome.</h1><p>Explore the bundled tuberculosis isolate data, compare phenotype distributions and run a reproducible baseline model.</p></div>', unsafe_allow_html=True)
    drugs = [d for d in ACTIVE_DRUG_CODES if (DATA / f"{d}.0050.labels.csv").exists() and (DATA / f"{d}.0050.features.h5").exists()]
    frames = [load_labels(d).assign(DRUG=d) for d in drugs]
    all_data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    cols=st.columns(4)
    for c,args in zip(cols,[("ANTIBIOTICS",len(drugs),"in the bundled demo"),("ISOLATES",50,"sample size per drug"),("FEATURES","31-mer","genomic feature matrix"),("PHENOTYPE","MIC","continuous and binary labels")]):
        with c: card(*args)
    st.markdown('<div class="section">A compact view of the demo</div><p class="subtle">Each drug has a matched 50-isolate label table and genomic k-mer feature matrix.</p>',unsafe_allow_html=True)
    st.markdown("**How to read this overview:** Antibiotics counts the drugs represented in the demo; isolates is the number of sample records per drug. A **31-mer** is a DNA pattern 31 bases long used as a model input. **MIC** is the lab measurement of the lowest tested drug concentration that prevents visible bacterial growth. The chart counts recorded susceptible, resistant, unknown, and missing labels for each drug.")
    left,right=st.columns([1.35,1])
    with left:
        if not all_data.empty and "BINARY_PHENOTYPE" in all_data:
            p=all_data.groupby(["DRUG","BINARY_PHENOTYPE"],dropna=False).size().reset_index(name="Isolates")
            p["Drug name"]=p.DRUG.map(DRUGS)
            p["Susceptibility"]=p.BINARY_PHENOTYPE.map(PHENOTYPE_NAMES).fillna("Not recorded")
            fig=px.bar(p,x="Drug name",y="Isolates",color="Susceptibility",barmode="stack",color_discrete_map={"Susceptible":"#83b7a3","Resistant":"#dd8268","Unknown / unclassified":"#d8c879","Not recorded":"#b8c4c3"},category_orders={"Susceptibility":["Susceptible","Resistant","Unknown / unclassified","Not recorded"]},labels={"Isolates":"Number of isolate records"})
            fig.update_layout(height=330,margin=dict(l=8,r=8,t=12,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#263b42",size=13),legend_title_text="Susceptibility",legend=dict(font=dict(color="#263b42"),title_font=dict(color="#263b42")),xaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#cbd8d5"),yaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#cbd8d5"),hoverlabel=dict(bgcolor="#ffffff",font=dict(color="#172b35",size=13),bordercolor="#cad7d4"))
            st.plotly_chart(fig,use_container_width=True)
            st.caption("Bars count isolate records with each binary susceptibility label. Unknown or missing labels are shown separately.")
    with right:
        st.markdown('<div class="section" style="margin-top:3px">What’s in the box</div>',unsafe_allow_html=True)
        st.markdown('<div class="note">This is a small research demo, useful for exploring workflow behavior. It is not a clinical decision tool.</div>',unsafe_allow_html=True)
        st.write("")
        st.markdown("**How to use this workspace**")
        st.markdown("""
        1. **Choose a drug** in the sidebar. Its short code is the identifier used in the dataset.
        2. **Explore the data** on the Data explorer page. Review MIC measurements and isolate details; use the search box to filter by isolate ID or study site.
        3. **Run a baseline** on the Model lab page. Select **Run baseline** to fit a model using genomic features and predict log₂ MIC with five-fold validation. Each isolate is held out for prediction once.
        4. **Review the results.** MAE summarizes the average prediction error. R² compares predictions with a simple average-value reference. The chart compares observed and predicted log₂ MIC for each isolate.
        5. **Download the predictions** as a CSV from the Model lab page.

        **Before you begin:** Overview summarizes the included sample data and phenotype counts. On Data explorer, expand **“What do these fields and values mean?”** for definitions. This is an exploratory demo; predictions are not clinical guidance.
        """)
    st.markdown('<div class="section">Drug panel</div>',unsafe_allow_html=True)
    panel=pd.DataFrame([{"Drug code":d,"Antibiotic":DRUGS[d],"Isolate records":len(load_labels(d)) if (DATA/f"{d}.0050.labels.csv").exists() else 0,"Model inputs":"31-base DNA patterns + MIC labels"} for d in drugs])
    st.caption("Drug code is the short identifier used in the research data files. Each isolate record represents one sample row for that drug.")
    show_table(panel)

def render_explorer(drug):
    df=load_labels(drug)
    st.markdown(f'<div class="section">{DRUGS[drug]} <span style="color:#71878a;font:13px DM Mono">/ {drug}</span></div><p class="subtle">Inspect isolate-level metadata and the phenotype distribution.</p>',unsafe_allow_html=True)
    st.markdown('<div class="section">Dataset tools</div><p class="subtle">Preview your own label CSV or download the bundled files for this drug.</p>',unsafe_allow_html=True)
    upload_col,labels_col,features_col=st.columns([1.4,1,1])
    with upload_col:
        uploaded=st.file_uploader("Upload a labels CSV",type=["csv"],help="Expected to contain fields such as UNIQUEID, LOG2MIC_NEW, and BINARY_PHENOTYPE. Uploaded files are previewed only; they do not replace the bundled data or feed the model.",key="upload_"+drug)
    with labels_col:
        labels_path=DATA/f"{drug}.0050.labels.csv"
        st.markdown("**Bundled labels**")
        st.download_button("Download CSV",data=labels_path.read_bytes(),file_name=f"{drug}.0050.labels.csv",mime="text/csv",help="Isolate metadata and phenotype labels for this drug.")
    with features_col:
        feature_path=DATA/f"{drug}.0050.features.h5"
        st.markdown("**Genomic features**")
        st.download_button("Download HDF5",data=feature_path.read_bytes(),file_name=f"{drug}.0050.features.h5",mime="application/x-hdf5",help="K-mer feature matrix used by the baseline model.")
    if uploaded is not None:
        try:
            user_df=pd.read_csv(uploaded)
            st.success(f"Loaded {len(user_df):,} rows and {len(user_df.columns):,} columns for preview.")
            show_table(user_df,100)
            st.caption("Preview is limited to the first 100 rows. The uploaded file remains in this session and is not saved to the project.")
        except Exception as e:
            st.error(f"Could not read this CSV: {e}")
    a,b,c=st.columns(3)
    with a: card("ISOLATES",len(df),"in sample table")
    with b: card("RESISTANT",int((df.BINARY_PHENOTYPE=="R").sum()) if "BINARY_PHENOTYPE" in df else "—","binary phenotype label")
    with c: card("SITES",df.SITEID.nunique() if "SITEID" in df else "—","represented in the sample")
    l,r=st.columns([1,1.3])
    with l:
        if "LOG2MIC_NEW" in df:
            z=df.copy(); z["LOG2MIC_NEW"]=pd.to_numeric(z.LOG2MIC_NEW,errors="coerce")
            z["Susceptibility"]=z.BINARY_PHENOTYPE.map(PHENOTYPE_NAMES).fillna("Not recorded")
            fig=px.histogram(z,x="LOG2MIC_NEW",color="Susceptibility",nbins=14,barmode="overlay",opacity=.8,color_discrete_map={"Susceptible":"#56a28c","Resistant":"#db765f","Unknown / unclassified":"#d8c879","Not recorded":"#b8c4c3"},labels={"LOG2MIC_NEW":"Log₂ MIC measurement","count":"Isolate records"})
            fig.update_layout(height=300,margin=dict(l=5,r=5,t=10,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#263b42",size=13),legend_title_text="Susceptibility",legend=dict(font=dict(color="#263b42"),title_font=dict(color="#263b42")),xaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#cbd8d5"),yaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#cbd8d5"),hoverlabel=dict(bgcolor="#ffffff",font=dict(color="#172b35",size=13),bordercolor="#cad7d4"))
            st.plotly_chart(fig,use_container_width=True)
            st.caption("Each bar counts isolates whose log₂ MIC falls in that range. Higher values indicate a higher measured MIC; bins are grouped by the recorded binary label.")
    with r:
        st.markdown("**Phenotype counts**")
        counts=df.BINARY_PHENOTYPE.map(PHENOTYPE_NAMES).fillna("Not recorded").value_counts(dropna=False).rename_axis("Susceptibility label").reset_index(name="Isolate records")
        show_table(counts)
        st.markdown("**Sample fields**")
        st.caption("MIC values describe the laboratory measurement; log₂ MIC expresses it on a base-2 logarithmic scale. Binary susceptibility is a separate categorized label. These are demo records.")
    fields=[c for c in ["UNIQUEID","SITEID","SPLIT","MIC_NEW","LOG2MIC_NEW","BINARY_PHENOTYPE","LINEAGE_NAME"] if c in df]
    st.markdown("**Isolate table**")
    query=st.text_input("Filter by isolate ID or site",key="filter_"+drug)
    show=df[fields].copy()
    if query:
        show=show[show.astype(str).apply(lambda s:s.str.contains(query,case=False,na=False)).any(axis=1)]
    display=show.rename(columns=FIELD_NAMES)
    if "Susceptibility" in display:
        display["Susceptibility"]=display["Susceptibility"].map(PHENOTYPE_NAMES).fillna("Not recorded")
    show_table(display,100)
    st.markdown("**What do these fields and values mean?**")
    st.markdown("""
        - **Isolate ID** — unique sample identifier in this dataset.
        - **Study site code** — identifier for the contributing study site; it is not a patient location label for general use.
        - **Data split** — `Train` means assigned to model fitting; `Test` means held out in the original example split.
        - **MIC measurement** — reported minimum inhibitory concentration (MIC). Values prefixed by `<` or `>` are bounded by the assay's tested range, rather than exact values.
        - **Log₂ MIC** — the log base 2 representation used as the model's numeric target; a one-unit difference is a two-fold difference on the original concentration scale.
        - **Susceptibility** — `Susceptible` and `Resistant` are recorded binary labels. `Unknown / unclassified` means the source value was `U`; `Not recorded` means no label was present.
        - **Bacterial lineage** — broad genetic ancestry classification for the isolate.

        A label is a recorded research phenotype, not a treatment recommendation.
        """)

def render_model(drug):
    st.markdown('<div class="section">Model lab</div><p class="subtle">Train a five-fold cross-validated regression baseline on the bundled k-mer matrix.</p>',unsafe_allow_html=True)
    st.markdown('<div class="note">This is an experimental teaching baseline, not a clinical tool. It selects the top 3% of genomic features inside each training fold, fits a Random Forest regressor, and predicts log₂ MIC for held-out isolates.</div>',unsafe_allow_html=True)
    if st.button(f"Run baseline · {DRUGS[drug]}",type="primary",use_container_width=False):
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.feature_selection import SelectKBest, f_regression
            from sklearn.model_selection import StratifiedKFold
            from sklearn.metrics import mean_absolute_error, r2_score
            df=load_labels(drug); X=load_features(drug)
            y=pd.to_numeric(df.LOG2MIC_NEW,errors="coerce")
            good=y.notna().to_numpy(); X=X.iloc[np.flatnonzero(good)]; df=df.loc[good].reset_index(drop=True); y=y.loc[good].reset_index(drop=True)
            strat=df.BINARY_PHENOTYPE.fillna("U").astype(str)
            counts=strat.value_counts()
            n_splits=min(5,int(counts.min()))
            if n_splits<2: raise ValueError("At least two isolates per phenotype class are required.")
            cv=StratifiedKFold(n_splits=n_splits,shuffle=True,random_state=40)
            pred=np.zeros(len(y),dtype=float)
            progress=st.progress(0,text="Fitting folds…")
            for i,(tr,te) in enumerate(cv.split(X,strat),start=1):
                k=max(1,min(X.shape[1],int(X.shape[1]*.03)))
                selector=SelectKBest(f_regression,k=k).fit(X.iloc[tr],y.iloc[tr])
                model=RandomForestRegressor(n_estimators=160,min_samples_leaf=2,max_features=.7,n_jobs=-1,random_state=40)
                model.fit(selector.transform(X.iloc[tr]),y.iloc[tr]); pred[te]=model.predict(selector.transform(X.iloc[te]))
                progress.progress(i/n_splits,text=f"Completed fold {i} of {n_splits}")
            result=df[[c for c in ["UNIQUEID","SITEID","BINARY_PHENOTYPE","LOG2MIC_NEW"] if c in df]].copy()
            result["PRED_LOG2MIC"]=np.round(pred,2)
            st.session_state["model_result"]=result
            st.session_state["model_drug"]=drug
            st.session_state["model_metrics"]={"mae":mean_absolute_error(y,pred),"r2":r2_score(y,pred),"n":len(y),"folds":n_splits}
        except ImportError as e:
            st.error(f"A modeling dependency is missing: {e}. Install requirements.txt and try again.")
        except Exception as e:
            st.error(f"Could not run the model: {e}")
    if "model_result" in st.session_state and st.session_state.get("model_drug")==drug:
        result=st.session_state["model_result"]; m=st.session_state["model_metrics"]
        st.markdown("**Cross-validation summary**")
        cols=st.columns(3)
        for c,args in zip(cols,[("MEAN ABSOLUTE ERROR",f"{m['mae']:.2f}","LOG₂ MIC units"),("R²",f"{m['r2']:.2f}","out-of-fold predictions"),("VALIDATION",f"{m['folds']} folds",f"{m['n']} isolates")]):
            with c: card(*args)
        result["Susceptibility"]=result.BINARY_PHENOTYPE.map(PHENOTYPE_NAMES).fillna("Not recorded")
        fig=px.scatter(result,x="LOG2MIC_NEW",y="PRED_LOG2MIC",color="Susceptibility",hover_data=[c for c in ["UNIQUEID","SITEID"] if c in result],color_discrete_map={"Susceptible":"#56a28c","Resistant":"#db765f","Unknown / unclassified":"#d8c879","Not recorded":"#b8c4c3"},labels={"LOG2MIC_NEW":"Observed log₂ MIC","PRED_LOG2MIC":"Predicted log₂ MIC"})
        fig.update_layout(height=360,margin=dict(l=10,r=10,t=15,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="white",font=dict(color="#263b42",size=13),legend=dict(font=dict(color="#263b42"),title_font=dict(color="#263b42")),xaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#9aadaa"),yaxis=dict(title_font=dict(color="#263b42"),tickfont=dict(color="#263b42"),gridcolor="#e2e9e7",zerolinecolor="#9aadaa"),hoverlabel=dict(bgcolor="#ffffff",font=dict(color="#172b35",size=13),bordercolor="#cad7d4"))
        st.plotly_chart(fig,use_container_width=True)
        st.caption("Each dot is one held-out isolate. Points nearer the diagonal have closer observed and predicted values; color shows its recorded susceptibility label.")
        st.caption(f"Mean absolute error (MAE) is the average absolute prediction error in log₂ MIC units; lower is closer. R² compares prediction error with a simple mean-value reference; 1 is a perfect fit, 0 is no improvement over that reference, and negative values are worse. Results summarize {m['n']} out-of-fold predictions from {m['folds']} folds.")
        display=result.rename(columns=FIELD_NAMES)
        display["Susceptibility"]=display["Susceptibility"].map(PHENOTYPE_NAMES).fillna("Not recorded")
        show_table(display,100)
        st.download_button("Download predictions as CSV",display.rename(columns={"Susceptibility":"Recorded susceptibility"}).to_csv(index=False).encode(),file_name=f"{drug}_baseline_predictions.csv",mime="text/csv",help="Save the table shown above, including observed and predicted log₂ MIC values.")

with st.sidebar:
    st.markdown("<div style='font:500 11px DM Mono;letter-spacing:2px;color:#587f82'>CRyPTIC · TB GENOMICS</div><h2 style='color:#000;margin:7px 0 22px'>Susceptibility<br>Lab</h2>",unsafe_allow_html=True)
    page=st.radio("WORKSPACE",["Overview","Data explorer","Model lab"],label_visibility="visible")
    st.markdown("---")
    st.caption("DEMO DATASET")
    catalog=get_drug_catalog()
    DRUGS.update(catalog)
    ACTIVE_DRUG_CODES=set(catalog)
    available=list(catalog)
    if available:
        drug=st.radio("SELECT DRUG",available,format_func=lambda d:f"{DRUGS[d]} · {d}",key="drug_choice")
    else:
        drug=None
        st.caption("No drug datasets are registered yet. Add a label CSV and feature HDF5 file below.")
    st.caption("Choose which drug's sample records or model results to view. The three-letter code is the dataset abbreviation.")
    st.markdown("**Add a drug option**")
    new_code=st.text_input("Drug code (for example, NEW)",max_chars=10).strip().upper()
    new_name=st.text_input("Drug name").strip()
    new_labels=st.file_uploader("Label data (.csv)",type=["csv"],key="new_labels_file")
    new_features=st.file_uploader("Feature data (.h5 or .hdf5)",type=["h5","hdf5"],key="new_features_file")
    if st.button("Add drug",key="add_drug"):
        if not new_code or not new_code.replace("_", "").isalnum() or not new_name:
            st.error("Enter a valid drug code and a display name.")
        elif not new_labels or not new_features:
            st.error("Choose both the label CSV and feature HDF5 files.")
        elif new_code in catalog:
            st.error("That drug code is already listed.")
        else:
            labels_path=DATA/f"{new_code}.0050.labels.csv"
            features_path=DATA/f"{new_code}.0050.features.h5"
            labels_path.write_bytes(new_labels.getvalue())
            features_path.write_bytes(new_features.getvalue())
            catalog[new_code]=new_name
            save_drug_catalog(catalog)
            st.success(f"Added {new_name}. Refresh the page to select it.")
    if available:
        st.markdown("**Remove a drug option**")
        remove_code=st.radio("Choose drug to remove",available,format_func=lambda d:f"{DRUGS[d]} · {d}",key="remove_drug_choice")
        if st.button("Remove selected option",key="remove_drug"):
            catalog.pop(remove_code,None)
            save_drug_catalog(catalog)
            st.success(f"Removed {remove_code} from the sidebar. Its files are kept in the data folder and can be re-added.")
    st.markdown("---")
    st.caption("Research prototype · sample data only")

if page=="Overview": render_overview()
elif drug is None:
    st.info("Add a complete drug dataset from the sidebar to begin.")
elif page=="Data explorer": render_explorer(drug)
else: render_model(drug)
