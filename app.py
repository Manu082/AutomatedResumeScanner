# app.py
import streamlit as st, os, tempfile, pandas as pd
import plotly.express as px
from parser import parse_resume, extract_text_from_pdf, extract_text_from_docx
from jd_parser import extract_keywords
from matcher import aggregate_scores_for_jd, compute_dashboard_stats
from exporter import results_to_dataframe
# from db import init_db, insert_resume

st.set_page_config(page_title="Automated Resume Scanner", layout="wide")
# init_db()

st.title("Automated Resume Scanner — Major Project")
st.caption("Candidate extraction, multi-JD matching, ATS scoring, ML skill extraction & dashboard stats.")

# Sidebar
st.sidebar.header("Settings")
use_keybert = st.sidebar.checkbox("Use KeyBERT (slower, more accurate)", value=False)
top_n_keywords = st.sidebar.number_input("Top N JD keywords", min_value=5, max_value=50, value=12)
upload_multiple_jds = st.sidebar.checkbox("Upload multiple JDs", value=True)
# save_to_db = st.sidebar.checkbox("Save parsed resumes to DB", value=False)

# 1️⃣ Upload JDs
st.header("Step 1: Upload Job Description(s)")
jd_files = st.file_uploader("Upload JD(s)", accept_multiple_files=upload_multiple_jds, type=["txt","pdf","docx"])
jd_text_manual = st.text_area("Or paste JD manually", height=150)
job_descriptions = {}

def _read_uploaded_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(file.getbuffer()); tmp.flush(); tmp.close()
    if ext==".pdf": txt=extract_text_from_pdf(tmp.name)
    elif ext in [".docx",".doc"]: txt=extract_text_from_docx(tmp.name)
    else: txt=open(tmp.name,"r",encoding="utf-8",errors="ignore").read()
    os.unlink(tmp.name)
    return txt

if jd_files:
    for f in jd_files:
        try: job_descriptions[f.name]=_read_uploaded_file(f)
        except Exception as e: st.warning(f"Could not process JD {f.name}: {e}")
if jd_text_manual.strip() and not jd_files: job_descriptions["Manual JD"]=jd_text_manual
if not job_descriptions: st.info("Upload/paste at least one JD."); st.stop()
st.success(f"Loaded {len(job_descriptions)} JD(s).")

# 2️⃣ Upload Resumes
st.header("Step 2: Upload Resumes")
uploaded_resumes = st.file_uploader("Upload resumes", accept_multiple_files=True, type=["pdf","docx","txt"])
if not uploaded_resumes: st.info("Upload resumes to analyze."); st.stop()

# Optional skills list
skills_csv = st.file_uploader("Optional: Upload skills list (TXT/CSV)")
skills_list = None
if skills_csv:
    try:
        content = skills_csv.getvalue().decode("utf-8",errors="ignore")
        skills_list=[line.strip() for line in content.splitlines() if line.strip()]
        st.sidebar.success(f"Loaded {len(skills_list)} skills from file.")
    except: st.sidebar.error("Failed to read skills list.")

# 3️⃣ Parse Resumes
st.header("Step 3: Parsing Resumes")
parsed_profiles=[]
progress = st.progress(0)
for i,resume_file in enumerate(uploaded_resumes):
    ext=os.path.splitext(resume_file.name)[1].lower()
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=ext)
    tmp.write(resume_file.getbuffer()); tmp.flush(); tmp.close()
    try:
        profile=parse_resume(tmp.name,skills_list=skills_list)
        profile["orig_filename"]=resume_file.name
        parsed_profiles.append(profile)
        # if save_to_db: insert_resume(profile)
    except Exception as e: st.error(f"Failed to parse {resume_file.name}: {e}")
    finally: os.unlink(tmp.name)
    progress.progress(int((i+1)/len(uploaded_resumes)*100))
st.success(f"Parsed {len(parsed_profiles)} resumes.")

# Show parsed table
st.subheader("Candidate Profiles")
df_parsed=pd.DataFrame([
    {"File":p.get("orig_filename"),
     "Name":os.path.splitext(p.get("orig_filename", "Unknown"))[0],
     "Email":p.get("email"),
     "Phone":p.get("phone"),
     "Education":"; ".join(p.get("education") or []),
     "Experience (Years)":p.get("experience_years"),
     "Skills":", ".join(p.get("skills") or [])} for p in parsed_profiles])
st.dataframe(df_parsed,use_container_width=True)

# 4️⃣ Matching & Dashboard
st.header("Step 4: Matching & ATS Scoring")
jd_tabs=st.tabs(list(job_descriptions.keys()))
all_results={}

for idx,(jd_title,jd_text) in enumerate(job_descriptions.items()):
    with jd_tabs[idx]:
        st.subheader(f"JD: {jd_title}")
        st.write(jd_text[:1000]+"..." if len(jd_text)>1000 else jd_text)
        with st.spinner("Extracting JD keywords..."):
            jd_keywords=extract_keywords(jd_text,method="keybert" if use_keybert else "tfidf",top_n=top_n_keywords)
        st.write("Extracted Keywords:",jd_keywords)
        edited_keywords=st.text_area("Edit Keywords (comma-separated)",value=", ".join(jd_keywords),key=f"kw_{idx}")
        final_keywords=[k.strip() for k in edited_keywords.split(",") if k.strip()]
        results=aggregate_scores_for_jd(parsed_profiles,final_keywords)
        all_results[jd_title]=results

        # Dashboard Stats & Charts
        st.markdown("---")
        st.subheader("Dashboard Analytics")
        stats = compute_dashboard_stats(results)
        
        # Display key metrics in columns
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Matching Score", f"{stats['avg_score']}%")
        with col2:
            st.metric("Average Experience (Years)", f"{stats['avg_experience']}")

        # Create and display charts
        if results:
            # Bar chart for candidate scores
            df_scores = pd.DataFrame(results)
            fig_scores = px.bar(df_scores.sort_values(by='score', ascending=False), 
                                x='name', 
                                y='score', 
                                title='Candidate Scores',
                                labels={'name': 'Candidate', 'score': 'Matching Score (%)'})
            st.plotly_chart(fig_scores, use_container_width=True)

            # Bar chart for most common skills
            if stats['common_skills']:
                df_skills = pd.DataFrame(stats['common_skills'], columns=['Skill', 'Count'])
                fig_skills = px.bar(df_skills, 
                                    x='Count', 
                                    y='Skill', 
                                    orientation='h', 
                                    title='Most Common Skills Found',
                                    labels={'Skill': 'Skill', 'Count': 'Number of Candidates'})
                fig_skills.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_skills, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Ranked Candidates")
        res_df=results_to_dataframe(results)
        st.dataframe(res_df,use_container_width=True)
        st.download_button(f"Download {jd_title} results",data=res_df.to_csv(index=False).encode("utf-8"),file_name=f"{jd_title}_results.csv")

st.success("Analysis complete. Review results or download CSVs.")