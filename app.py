from pathlib import Path
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
PHENOTYPE_NAMES = {"S": "Susceptible", "R": "Resistant", "U": "Unknown / unclassified"}
FIELD_NAMES = {
    "UNIQUEID": "Isolate ID", "SITEID": "Study site code", "SPLIT": "Data split",
    "MIC_NEW": "MIC measurement", "LOG2MIC_NEW": "Log₂ MIC", "BINARY_PHENOTYPE": "Susceptibility",
    "LINEAGE_NAME": "Bacterial lineage", "PRED_LOG2MIC": "Predicted log₂ MIC",
}
st.set_page_config(page_title="TB Susceptibility Lab", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{--ink:#172b35;--muted:#667b81;--line:#dce6e5;--paper:#f5f8f6;--teal:#087e79;--lime:#d9edb2}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--paper)}
[data-testid="stAppViewContainer"]{color:#172b35}
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"]{color:#334b52}
[data-testid="stSidebar"]{background:#18363b;color:#f2f7f3}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#ffffff!important;font-size:14px!important;line-height:1.5!important}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] span{color:#172b35!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#fff!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{color:#f0f5f2!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:#f0f5f2!important}
[data-testid="stDataFrame"]{color:#172b35!important}
[data-testid="stDataFrame"] *{color:#172b35!important}
.stTextInput input{color:#172b35!important;background:#fff!important}
.stTextInput input::placeholder{color:#65797e!important;opacity:1}
.stSelectbox [data-baseweb="select"]>div{background:#fff!important}
.stSelectbox [data-baseweb="select"] *{color:#172b35!important}
.stExpander summary p{color:#172b35!important}
.stButton button{color:#172b35}
.stButton button[kind="primary"]{color:#fff!important}
.hero{background:#18363b;border-radius:18px;padding:34px 38px;color:#f5f8f3;margin:4px 0 22px;position:relative;overflow:hidden}
.hero:after{content:'◉';position:absolute;right:42px;top:-55px;font-size:230px;color:#285257;opacity:.55}
.eyebrow{font:500 11px 'DM Mono';letter-spacing:2px;text-transform:uppercase;color:#b8d98e}
.hero h1{font-size:37px;line-height:1.12;letter-spacing:-1.4px;margin:12px 0 8px;color:#fff;max-width:670px}
.hero p{color:#c5d6d0;max-width:620px;margin:0;font-size:15px}
.metric{background:#fff;border:1px solid var(--line);border-radius:13px;padding:18px 20px;min-height:112px}
.metric-label{font:11px 'DM Mono';letter-spacing:1px;text-transform:uppercase;color:#52676c}
.metric-value{font-size:29px;font-weight:700;letter-spacing:-1px;margin:8px 0 1px;color:var(--ink)}
.metric-note{font-size:12px;color:#52676c}
.section{font-size:21px;font-weight:700;letter-spacing:-.5px;margin:22px 0 4px}
.subtle{font-size:13px;color:#52676c;margin:0 0 14px}
.note{background:#eaf2dd;border-left:3px solid #8aad54;padding:12px 15px;border-radius:0 8px 8px 0;color:#3c5742;font-size:13px}
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

def render_overview():
    st.markdown('<div class="hero"><div class="eyebrow">Research workspace · CRyPTIC demo</div><h1>Drug resistance, seen through the genome.</h1><p>Explore the bundled tuberculosis isolate data, compare phenotype distributions and run a reproducible baseline model.</p></div>', unsafe_allow_html=True)
    drugs = [d for d in DRUGS if (DATA / f"{d}.0050.labels.csv").exists()]
    frames = [load_labels(d).assign(DRUG=d) for d in drugs]
    all_data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    cols=st.columns(4)
    for c,args in zip(cols,[("ANTIBIOTICS",len(drugs),"in the bundled demo"),("ISOLATES",50,"sample size per drug"),("FEATURES","31-mer","genomic feature matrix"),("PHENOTYPE","MIC","continuous and binary labels")]):
        with c: card(*args)
    st.markdown('<div class="section">A compact view of the demo</div><p class="subtle">Each drug has a matched 50-isolate label table and genomic k-mer feature matrix.</p>',unsafe_allow_html=True)
    with st.expander("How to read this overview"):
        st.markdown("**Antibiotics** counts the drugs represented in the demo; **isolates** is the number of sample records per drug. **31-mer** refers to DNA patterns 31 bases long used as model features. **MIC** is the lab measurement of the lowest tested drug concentration that prevents visible bacterial growth. The chart counts recorded susceptible, resistant, unknown, and missing labels for each drug.")
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
    st.dataframe(panel,hide_index=True,use_container_width=True)

def render_explorer(drug):
    df=load_labels(drug)
    st.markdown(f'<div class="section">{DRUGS[drug]} <span style="color:#71878a;font:13px DM Mono">/ {drug}</span></div><p class="subtle">Inspect isolate-level metadata and the phenotype distribution.</p>',unsafe_allow_html=True)
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
        st.dataframe(counts,hide_index=True,use_container_width=True)
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
    st.dataframe(display,hide_index=True,use_container_width=True,height=310)
    with st.expander("What do these fields and values mean?"):
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
        st.dataframe(display,hide_index=True,use_container_width=True)
        st.download_button("Download predictions as CSV",display.rename(columns={"Susceptibility":"Recorded susceptibility"}).to_csv(index=False).encode(),file_name=f"{drug}_baseline_predictions.csv",mime="text/csv",help="Save the table shown above, including observed and predicted log₂ MIC values.")

with st.sidebar:
    st.markdown("<div style='font:500 11px DM Mono;letter-spacing:2px;color:#b8d98e'>CRyPTIC · TB GENOMICS</div><h2 style='color:white;margin:7px 0 22px'>Susceptibility<br>Lab</h2>",unsafe_allow_html=True)
    page=st.radio("WORKSPACE",["Overview","Data explorer","Model lab"],label_visibility="visible")
    st.markdown("---")
    st.caption("DEMO DATASET")
    available=[d for d in DRUGS if (DATA/f"{d}.0050.labels.csv").exists()]
    drug=st.selectbox("Antibiotic",available,format_func=lambda d:f"{DRUGS[d]}  ·  {d}")
    st.caption("Choose which drug's sample records or model results to view. The three-letter code is the dataset abbreviation.")
    st.markdown("---")
    st.caption("Research prototype · sample data only")

if page=="Overview": render_overview()
elif page=="Data explorer": render_explorer(drug)
else: render_model(drug)
