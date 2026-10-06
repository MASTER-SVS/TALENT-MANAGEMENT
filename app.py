from __future__ import annotations
import json
from io import BytesIO
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
from services.core import (BASE_DIR, ROLE_CATALOG, LEVELS, init_db, register, login, get_profile, save_profile,
    list_skills, add_skill, delete_skill, add_assessment, get_assessments, save_progress, get_progress,
    profile_completion, gap_analysis, recommendations, profile_analysis, role_match, export_user_data)
from services.reports import create_report

load_dotenv(BASE_DIR / ".env")
st.set_page_config(page_title="TalentSphere", page_icon="🌱", layout="wide")
init_db()

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
.stApp {background: #f5f8f8; color:#182b36; font-family:'DM Sans', sans-serif}
h1,h2,h3 {font-family:'Manrope',sans-serif; color:#173343}
[data-testid="stSidebar"] {background:#102b3b}
[data-testid="stSidebar"] * {color:#edf5f5}
.hero {background:linear-gradient(120deg,#123748,#1d6870);padding:28px 32px;border-radius:18px;color:white;margin-bottom:20px}
.hero h1,.hero p {color:white;margin:0}
div[data-testid="stMetric"] {background:white;border:1px solid #e4ecee;border-radius:14px;padding:15px}
div.stButton>button {border-radius:10px;font-weight:600}
</style>""", unsafe_allow_html=True)

if "user" not in st.session_state: st.session_state.user = None

def auth_screen():
    st.markdown('<div class="hero"><h1>TalentSphere</h1><p>A practical space to map your skills, career direction, and next steps.</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1,1])
    with left:
        st.subheader("Sign in")
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            user = login(email, password)
            if user: st.session_state.user = user; st.rerun()
            else: st.error("Email or password did not match.")
    with right:
        st.subheader("Create an account")
        with st.form("register"):
            name = st.text_input("Full name")
            new_email = st.text_input("Work or personal email")
            new_password = st.text_input("Password (8+ characters)", type="password")
            submit_reg = st.form_submit_button("Create account", use_container_width=True)
        if submit_reg:
            ok, msg = register(name, new_email, new_password)
            (st.success if ok else st.error)(msg)
    st.caption("Your profile and career information are private to your account and stored in a local SQLite database.")

if not st.session_state.user:
    auth_screen(); st.stop()

user = st.session_state.user
uid = user["id"]
profile = get_profile(uid)
skills = list_skills(uid)
with st.sidebar:
    st.markdown("### 🌱 TalentSphere")
    st.caption(f"Signed in as {user['name']}")
    page = st.radio("Workspace", ["Dashboard", "My Profile", "Resume Studio", "Skills & Assessment", "Career Direction", "Role Match & Gaps", "Career Coach", "Growth Progress", "Career Report", "Settings"], label_visibility="collapsed")
    if st.button("Sign out", use_container_width=True):
        st.session_state.user = None; st.rerun()

def analysis_bundle():
    result = profile_analysis(profile, skills)
    result["match"] = role_match(profile.get("target_role", ""), skills, float(profile.get("years_experience") or 0))
    return result

if page == "Dashboard":
    completion, missing = profile_completion(profile, skills)
    analysis = analysis_bundle()
    st.markdown(f'<div class="hero"><h1>Good to see you, {user["name"].split()[0]}</h1><p>Build a clearer view of where you are and what comes next.</p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Profile completion", f"{completion}%")
    c2.metric("Profile strength", f"{analysis['score']}/100")
    c3.metric("Target role match", f"{analysis['match']}%")
    c4.metric("Skills recorded", len(skills))
    st.progress(completion/100)
    col1,col2 = st.columns([1,1])
    with col1:
        st.subheader("Your next useful actions")
        for rec in recommendations(profile, skills)[:4]:
            with st.container(border=True): st.markdown(f"**{rec['priority']} · {rec['title']}**\n\n{rec['description']}")
    with col2:
        st.subheader("Career snapshot")
        st.write(f"**Current role:** {profile.get('job_title') or 'Add your current role'}")
        st.write(f"**Target:** {profile.get('target_role') or 'Choose a target role'}")
        if skills:
            df = pd.DataFrame(skills)
            st.plotly_chart(px.bar(df, x="name", y="years", color="category", title="Skills and years of experience", height=300), use_container_width=True)
        else: st.info("Add a few skills to see your career snapshot.")
    if missing:
        with st.expander("Profile sections to complete"):
            st.write(" · ".join(missing))

elif page == "My Profile":
    st.title("My professional profile")
    with st.form("profile_form"):
        a,b = st.columns(2)
        with a:
            st.text_input("Full name", value=user["name"], disabled=True)
            phone=st.text_input("Phone", value=profile.get("phone", "")); location=st.text_input("Location", value=profile.get("location", ""))
            job=st.text_input("Current job title", value=profile.get("job_title", "")); company=st.text_input("Company", value=profile.get("company", ""))
            department=st.text_input("Department", value=profile.get("department", "")); industry=st.text_input("Industry", value=profile.get("industry", ""))
        with b:
            employment=st.selectbox("Employment type", ["Full-time","Part-time","Contract","Self-employed","Other"], index=["Full-time","Part-time","Contract","Self-employed","Other"].index(profile.get("employment_type") or "Full-time"))
            years=st.number_input("Years of experience", min_value=0.0, max_value=60.0, value=float(profile.get("years_experience") or 0), step=.5)
            linkedin=st.text_input("LinkedIn URL", value=profile.get("linkedin", "")); github=st.text_input("GitHub URL", value=profile.get("github", "")); portfolio=st.text_input("Portfolio URL", value=profile.get("portfolio", ""))
            education=st.text_area("Education", value=profile.get("education", ""), placeholder="Degree · Institution · Year")
            certifications=st.text_area("Certifications", value=profile.get("certifications", ""))
        summary=st.text_area("Professional summary", value=profile.get("summary", ""), height=100)
        experience=st.text_area("Experience", value=profile.get("experience", ""), height=130, placeholder="Role, company, dates, responsibilities, measurable outcomes")
        projects=st.text_area("Projects and achievements", value=profile.get("projects", ""), height=100)
        if st.form_submit_button("Save profile", type="primary"):
            save_profile(uid, locals() | {"phone":phone,"location":location,"job_title":job,"company":company,"department":department,"industry":industry,"employment_type":employment,"years_experience":years,"linkedin":linkedin,"github":github,"portfolio":portfolio,"education":education,"certifications":certifications,"summary":summary,"experience":experience,"projects":projects})
            st.success("Profile saved."); st.rerun()
    completion, missing = profile_completion(profile, skills)
    st.progress(completion/100, text=f"Profile completion {completion}%")
    if missing: st.caption("Still to add: " + ", ".join(missing))

elif page == "Resume Studio":
    st.title("Resume Studio")
    st.caption("Create an ATS-friendly PDF from information you have entered. Check the draft before sending it to an employer.")
    upload = st.file_uploader("Import an existing resume (PDF or DOCX)", type=["pdf","docx"])
    if upload:
        try:
            if upload.name.lower().endswith(".pdf"): text = "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
            else: text = "\n".join(p.text for p in Document(upload).paragraphs)
            if st.button("Save extracted resume text"):
                save_profile(uid,{"resume_text":text}); st.success("Resume text saved for alignment review."); st.rerun()
            st.text_area("Extracted text preview", text, height=180)
        except Exception as exc: st.error(f"Could not read this file. Check that it is a valid PDF or DOCX. Details: {exc}")
    c1,c2=st.columns(2)
    with c1: st.subheader("Resume content"); st.write(profile.get("summary") or "Add a summary in My Profile."); st.write("**Skills:** " + (", ".join(x["name"] for x in skills) or "None added")); st.write(profile.get("experience") or "Add experience details in My Profile.")
    with c2:
        st.subheader("Resume alignment")
        resume=(profile.get("resume_text") or "").lower(); role_skills=ROLE_CATALOG.get(profile.get("target_role", ""),{}).get("skills",{})
        if resume:
            matched=[s for s in role_skills if s.lower() in resume]; missing_kw=[s for s in role_skills if s.lower() not in resume]
            score=round(100*len(matched)/max(1,len(role_skills)))
            st.metric("Target keyword alignment",f"{score}%")
            st.write("Found: " + (", ".join(matched) or "No target keywords detected")); st.write("Potential keywords to address truthfully: " + (", ".join(missing_kw) or "None"))
        else: st.info("Import a resume to compare its text with your target role.")
    st.subheader("ATS resume preview")
    st.markdown(f"### {user['name']}\n{profile.get('location','')} · {profile.get('phone','')} · {user['email']}\n\n**Professional Summary**\n\n{profile.get('summary') or 'Add a professional summary.'}\n\n**Skills**\n\n{', '.join(s['name']+' — '+s['proficiency'] for s in skills) or 'Add skills.'}\n\n**Experience**\n\n{profile.get('experience') or 'Add experience.'}\n\n**Education**\n\n{profile.get('education') or 'Add education.'}\n\n**Certifications**\n\n{profile.get('certifications') or 'Add certifications.'}\n\n**Projects**\n\n{profile.get('projects') or 'Add projects.'}\n\n**Links**\n\n{profile.get('linkedin','')} · {profile.get('github','')} · {profile.get('portfolio','')}")
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=letter); y=740
    lines=[user["name"],f"{profile.get('location','')} | {profile.get('phone','')} | {user['email']}","", "PROFESSIONAL SUMMARY",profile.get("summary") or "", "", "SKILLS",", ".join(s["name"]+" ("+s["proficiency"]+")" for s in skills), "", "EXPERIENCE",profile.get("experience") or "", "", "EDUCATION",profile.get("education") or "", "", "CERTIFICATIONS",profile.get("certifications") or "", "", "PROJECTS",profile.get("projects") or "", "", "LINKS", " | ".join(profile.get(k,"") for k in ("linkedin","github","portfolio"))]
    for para in lines:
        for line in para.splitlines() or [""]:
            if y<55: c.showPage(); y=740
            c.setFont("Helvetica-Bold" if para in ["PROFESSIONAL SUMMARY","SKILLS","EXPERIENCE","EDUCATION","CERTIFICATIONS","PROJECTS","LINKS",user["name"]] else "Helvetica", 14 if para==user["name"] else 10)
            for chunk in [line[i:i+95] for i in range(0,max(1,len(line)),95)]: c.drawString(48,y,chunk); y-=15
    c.save(); st.download_button("Download ATS resume PDF",buf.getvalue(),file_name="talentsphere_resume.pdf",mime="application/pdf",type="primary")

elif page == "Skills & Assessment":
    st.title("Skills and assessments")
    with st.form("skill_add"):
        a,b,c,d=st.columns([2,1.4,1,1]); name=a.text_input("Skill"); category=b.selectbox("Category",["Technical","Domain","Soft Skill","Leadership","Tool","Business"]); proficiency=c.selectbox("Proficiency",list(LEVELS)); yrs=d.number_input("Years",0.0,50.0,0.0,.5)
        if st.form_submit_button("Add skill"):
            ok,msg=add_skill(uid,name,category,proficiency,yrs); (st.success if ok else st.warning)(msg); st.rerun()
    if skills:
        st.dataframe(pd.DataFrame(skills)[["name","category","proficiency","years"]], use_container_width=True, hide_index=True)
        ids={f"{s['name']} · {s['proficiency']}":s["id"] for s in skills}; selected=st.selectbox("Remove a skill",["Select"]+list(ids))
        if selected!="Select" and st.button("Remove selected skill"): delete_skill(uid,ids[selected]); st.rerun()
    st.divider(); st.subheader("Self-assessment")
    with st.form("assessment"):
        cat=st.selectbox("Capability area",["Technical","Communication","Leadership","Problem solving","Domain knowledge","Professional effectiveness"]); score=st.slider("Self-rated confidence",0,100,70); submitted=st.form_submit_button("Record assessment")
    if submitted: add_assessment(uid,cat,score); st.success("Assessment recorded."); st.rerun()
    assessments=get_assessments(uid)
    if assessments: st.dataframe(pd.DataFrame(assessments)[["category","score","created_at"]],use_container_width=True,hide_index=True)

elif page == "Career Direction":
    st.title("Career direction")
    with st.form("goal"):
        current=st.text_input("Current role",value=profile.get("job_title", "")); target=st.selectbox("Target role",["Choose a role"]+list(ROLE_CATALOG),index=(list(ROLE_CATALOG).index(profile["target_role"])+1 if profile.get("target_role") in ROLE_CATALOG else 0)); level=st.selectbox("Target level",["Individual contributor","Senior","Lead","Manager","Director"],index=["Individual contributor","Senior","Lead","Manager","Director"].index(profile.get("target_level") or "Senior")); timeline=st.selectbox("Target timeline",["3–6 months","6–12 months","1–2 years","Exploring"]); industry=st.text_input("Target industry",value=profile.get("target_industry", "")); goal=st.text_area("What does career growth mean to you?",value=profile.get("career_goal", ""))
        if st.form_submit_button("Save career direction",type="primary"):
            save_profile(uid,{"job_title":current,"target_role":"" if target=="Choose a role" else target,"target_level":level,"timeline":timeline,"target_industry":industry,"career_goal":goal}); st.success("Career direction saved."); st.rerun()
    if profile.get("target_role"):
        st.info(ROLE_CATALOG[profile["target_role"]]["criteria"])

elif page == "Role Match & Gaps":
    st.title("Target role match and skill gaps")
    target=profile.get("target_role")
    if not target: st.info("Set a target role under Career Direction to unlock role matching.")
    else:
        gaps=gap_analysis(target,skills); match=role_match(target,skills,float(profile.get("years_experience") or 0)); st.metric(f"Match for {target}",f"{match}%"); st.progress(match/100)
        levels={0:"Not recorded",1:"Beginner",2:"Intermediate",3:"Advanced",4:"Expert"}
        gapdf=pd.DataFrame([{ "Skill":g["skill"],"Current":levels[g["current"]],"Required":levels[g["required"]],"Gap":g["gap"],"Priority":g["priority"]} for g in gaps]); st.dataframe(gapdf,use_container_width=True,hide_index=True)
        st.caption(ROLE_CATALOG[target]["criteria"])
        st.subheader("Suggested development actions")
        for item in recommendations(profile,skills):
            with st.container(border=True): st.markdown(f"**{item['priority']} · {item['title']}**\n\n{item['description']}")

elif page == "Career Coach":
    st.title("Career coach")
    st.caption("Rule-based coaching is available offline. Guidance uses the profile details and skills you provide; it does not invent qualifications.")
    question=st.text_area("What would you like help with?",placeholder="For example: What should I focus on over the next six months?")
    if st.button("Get guidance",type="primary"):
        if not question.strip(): st.warning("Write a question first.")
        else:
            a=analysis_bundle(); recs=recommendations(profile,skills); st.markdown(f"**Your current picture:** profile strength {a['score']}/100, target role alignment {a['match']}%. ")
            st.markdown("**A practical next move:** " + recs[0]["description"])
            st.markdown("**Keep in view:** " + ("; ".join(a["weaknesses"]) if a["weaknesses"] else "Continue gathering evidence of your impact."))
            st.caption("Local guidance mode · Add GEMINI_API_KEY to configure a future LLM integration.")

elif page == "Growth Progress":
    st.title("Growth progress")
    st.caption("Choose a development action and update its completion as you make progress.")
    with st.form("progress_form"):
        item=st.text_input("Goal or action",placeholder="Complete a cloud fundamentals course"); percent=st.slider("Completion",0,100,0); saved=st.form_submit_button("Save progress")
    if saved and item.strip(): save_progress(uid,item.strip(),percent); st.success("Progress updated."); st.rerun()
    progress=get_progress(uid)
    if progress:
        df=pd.DataFrame(progress); st.dataframe(df[["item","percent","status","updated_at"]],use_container_width=True,hide_index=True); st.plotly_chart(px.bar(df,x="item",y="percent",range_y=[0,100],title="Development action progress"),use_container_width=True)
        st.metric("Average tracked progress",f"{round(df.percent.mean())}%")
    else: st.info("Your progress tracker is ready. Add the first action above.")

elif page == "Career Report":
    st.title("Career growth report")
    st.caption("Each download is generated from your latest saved profile, skill, assessment, and progress data.")
    a=analysis_bundle(); gaps=gap_analysis(profile.get("target_role", ""),skills); recs=recommendations(profile,skills); assessments=get_assessments(uid); progress=get_progress(uid)
    st.subheader("Report preview")
    x,y,z=st.columns(3); x.metric("Profile",f"{a['completion']}%"); y.metric("Strength",f"{a['score']}/100"); z.metric("Role alignment",f"{a['match']}%")
    st.write("**Strengths:** " + "; ".join(a["strengths"])); st.write("**Focus areas:** " + "; ".join(a["weaknesses"]))
    st.dataframe(pd.DataFrame([{ "Skill":g["skill"],"Gap":g["gap"],"Priority":g["priority"]} for g in gaps]),use_container_width=True,hide_index=True)
    pdf=create_report(profile,skills,a,gaps,recs,assessments,progress)
    st.download_button("Download complete career growth report PDF",pdf,file_name="employee_career_growth_report.pdf",mime="application/pdf",type="primary")
    payload=json.dumps(export_user_data(uid),indent=2,default=str).encode()
    st.download_button("Download my data (JSON)",payload,file_name="talentsphere_employee_data.json",mime="application/json")

elif page == "Settings":
    st.title("Settings and privacy")
    st.write(f"Account: **{user['email']}**")
    st.write("Your app stores data in a local SQLite database. Keep your database file and backups private.")
    st.code(str(BASE_DIR / "data" / "talentsphere.db"),language=None)
    st.caption("For a hosted deployment, configure persistent storage, HTTPS, backups, and a managed secrets store before inviting employees.")
