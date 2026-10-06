from __future__ import annotations
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def create_report(profile, skills, analysis, gaps, recs, assessments, progress) -> bytes:
    """Build a current-data, printable employee career report in memory."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    story = [Paragraph("TalentSphere | Career Growth Report", styles["Title"]), Spacer(1, 12),
             Paragraph(f"Prepared for {profile.get('name','Employee')} · {profile.get('email','')} · {profile.get('updated_at','')[:10]}", styles["Normal"]), Spacer(1, 18),
             Paragraph("Career snapshot", styles["Heading2"]),
             Paragraph(f"Current role: {profile.get('job_title') or 'Not provided'} &nbsp;&nbsp; Target: {profile.get('target_role') or 'Not selected'}<br/>Employer: {profile.get('company') or 'Not provided'} &nbsp;&nbsp; Experience: {profile.get('years_experience',0)} years<br/>Career goal: {profile.get('career_goal') or 'Not provided'}", styles["BodyText"]), Spacer(1, 12),
             Paragraph(f"Profile completion: {analysis['completion']}% &nbsp;&nbsp; Profile strength: {analysis['score']}/100 &nbsp;&nbsp; Role match: {analysis['match']}%", styles["Heading3"]),
             Paragraph("Profile assessment", styles["Heading2"]),
             Paragraph("Strengths: " + "; ".join(analysis["strengths"]), styles["BodyText"]),
             Paragraph("Focus areas: " + "; ".join(analysis["weaknesses"]), styles["BodyText"]), Spacer(1, 10),
             Paragraph("Skill gap analysis", styles["Heading2"])]
    rows = [["Skill", "Current", "Required", "Gap", "Priority"]]
    levels = {0:"Not recorded", 1:"Beginner", 2:"Intermediate", 3:"Advanced", 4:"Expert"}
    rows += [[g["skill"], levels.get(g["current"], "Not recorded"), levels[g["required"]], str(g["gap"]), g["priority"]] for g in gaps]
    table = Table(rows, repeatRows=1, colWidths=[150, 90, 85, 45, 85])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#152C3B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#D7E0E5")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F7F8")]),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8)]))
    story += [table, Spacer(1, 12), Paragraph("Recorded skills", styles["Heading2"])]
    story.append(Paragraph(", ".join(f"{s['name']} ({s['proficiency']})" for s in skills) or "No skills recorded yet.", styles["BodyText"]))
    story += [Spacer(1, 12), Paragraph("Recommended actions", styles["Heading2"])]
    for item in recs:
        story.append(Paragraph(f"<b>{item['priority']}: {item['title']}</b> — {item['description']}", styles["BodyText"]))
        story.append(Spacer(1, 5))
    if assessments:
        story += [Spacer(1, 8), Paragraph("Assessment history", styles["Heading2"]), Paragraph("; ".join(f"{a['category']}: {a['score']}% ({a['created_at'][:10]})" for a in assessments), styles["BodyText"])]
    if progress:
        story += [Spacer(1, 8), Paragraph("Growth progress", styles["Heading2"]), Paragraph("; ".join(f"{p['item']}: {p['percent']}%" for p in progress), styles["BodyText"])]
    story += [PageBreak(), Paragraph("Career action plan", styles["Heading1"]),
              Paragraph("Next 0–3 months: choose one high-priority gap and complete a small work-based project that demonstrates it.", styles["BodyText"]), Spacer(1,8),
              Paragraph("3–6 months: seek feedback, update your resume with verified outcomes, and review progress against your target role.", styles["BodyText"]), Spacer(1,8),
              Paragraph("6–12 months: take on broader ownership and record evidence of collaboration, delivery, and impact.", styles["BodyText"]), Spacer(1,16),
              Paragraph("Summary", styles["Heading2"]),
              Paragraph(f"Your profile currently shows {analysis['completion']}% completion and {analysis['match']}% alignment with {profile.get('target_role') or 'your target role'}. Focus first on: " + "; ".join(analysis["recommendations"][:3]) + ". Reassess after you have added new evidence.", styles["BodyText"])]
    doc.build(story)
    return output.getvalue()
