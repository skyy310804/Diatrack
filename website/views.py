from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from openpyxl import Workbook
from . import db
from .models import Glucose, Carbs, Insulin
from io import BytesIO
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
from werkzeug.utils import secure_filename
import os

views = Blueprint("views", __name__)


# ==========================
# DASHBOARD
# ==========================

@views.route("/")
@login_required
def home():

    # ======================================================
    # FETCH USER DATA
    # ======================================================

    glucose_logs = (
        Glucose.query.filter_by(user_id=current_user.id)
        .order_by(Glucose.recorded_at.asc())
        .all()
    )

    total_logs = len(glucose_logs)

    chart_labels = [
    log.recorded_at.strftime("%b %d")
    for log in glucose_logs[-7:]
        ]

    chart_values = [
    log.glucose_level
    for log in glucose_logs[-7:]
        ]

    carb_logs = (
        Carbs.query.filter_by(user_id=current_user.id)
        .order_by(Carbs.recorded_at.desc())
        .all()
    )

    insulin_logs = (
        Insulin.query.filter_by(user_id=current_user.id)
        .order_by(Insulin.recorded_at.desc())
        .all()
    )

    # ======================================================
    # BASIC STATISTICS
    # ======================================================

    total_glucose_logs = len(glucose_logs)
    weekly_logs = total_glucose_logs

    avg_glucose = (
        round(
            sum(g.glucose_level for g in glucose_logs) /
            total_glucose_logs
        )
        if total_glucose_logs
        else 0
    )

    highest_glucose = max(
        (g.glucose_level for g in glucose_logs),
        default=0
    )

    lowest_glucose = min(
        (g.glucose_level for g in glucose_logs),
        default=0
    )

    total_carbs = sum(c.carbs for c in carb_logs)

    total_insulin = round(
        sum(i.units for i in insulin_logs),
        1
    )

    # ======================================================
    # TODAY'S VALUES
    # ======================================================

    today_glucose = (
        glucose_logs[-1].glucose_level
        if glucose_logs
        else 0
    )

    today_carbs = (
        carb_logs[0].carbs
        if carb_logs
        else 0
    )

    today_insulin = (
        insulin_logs[0].units
        if insulin_logs
        else 0
    )

    # ======================================================
    # RECENT TABLES
    # ======================================================

    recent_glucose = glucose_logs[-5:][::-1]
    recent_carbs = carb_logs[:5]
    recent_insulin = insulin_logs[:5]

    # ======================================================
    # TIME IN RANGE
    # ======================================================

    if glucose_logs:

        in_range = sum(
            1
            for g in glucose_logs
            if 70 <= g.glucose_level <= 180
        )

        time_in_range = round(
            (in_range / total_glucose_logs) * 100
        )

    else:

        time_in_range = 0

    # ======================================================
    # HEALTH SCORE
    # ======================================================

    consistency_score = min(
        100,
        weekly_logs * 10
    )

    glucose_penalty = sum(
        5 if g.glucose_level < 70
        else 3 if g.glucose_level > 180
        else 0
        for g in glucose_logs
    )

    health_score = round(
        (time_in_range * 0.60)
        +
        (consistency_score * 0.40)
        -
        glucose_penalty
    )

    health_score = max(
        0,
        min(100, health_score)
    )
        # ======================================================
    # GLUCOSE STABILITY
    # ======================================================

    if len(glucose_logs) >= 2:

        values = [g.glucose_level for g in glucose_logs]

        difference = max(values) - min(values)

        if difference <= 30:
            stability = "Very Stable"

        elif difference <= 60:
            stability = "Stable"

        elif difference <= 100:
            stability = "Moderate"

        else:
            stability = "Unstable"

    else:
        stability = "Not Enough Data"

    # ======================================================
    # LOGGING CONSISTENCY
    # ======================================================

    if weekly_logs >= 14:
        consistency = "Excellent"

    elif weekly_logs >= 10:
        consistency = "Good"

    elif weekly_logs >= 5:
        consistency = "Fair"

    else:
        consistency = "Needs Improvement"

    # ======================================================
    # STATUS COLOR
    # ======================================================

    if health_score >= 85:
        status_color = "success"

    elif health_score >= 65:
        status_color = "primary"

    elif health_score >= 40:
        status_color = "warning"

    else:
        status_color = "danger"

    # ======================================================
    # RISK LEVEL
    # ======================================================

    if avg_glucose == 0:
        risk = "No Data"

    elif avg_glucose < 70:
        risk = "Low Glucose"

    elif avg_glucose <= 180:
        risk = "Healthy"

    else:
        risk = "High Glucose"

    # ======================================================
    # GLUCOSE TREND
    # ======================================================

    trend = "→"

    if len(glucose_logs) >= 2:

        previous = glucose_logs[-2].glucose_level
        latest = glucose_logs[-1].glucose_level

        if latest > previous:
            trend = "↑"

        elif latest < previous:
            trend = "↓"

    # ======================================================
    # SMART RECOMMENDATION
    # ======================================================

    if avg_glucose == 0:

        recommendation = (
            "Start logging your glucose readings to receive personalized insights."
        )

    elif avg_glucose < 70:

        recommendation = (
            "Average glucose is below the target range. Monitor for hypoglycemia and consult your healthcare provider if low readings continue."
        )

    elif avg_glucose <= 180:

        recommendation = (
            "Your glucose readings are within the recommended target range. Continue maintaining your current routine."
        )

    else:

        recommendation = (
            "Average glucose is above the recommended target range. Review meals, insulin timing, physical activity, and consult your healthcare provider if needed."
        )

    # ======================================================
    # CHART DATA
    # ======================================================

    chart_labels = [
    log.recorded_at.strftime("%b %d")
    for log in glucose_logs[-7:]
        ]

    chart_values = [
    log.glucose_level
    for log in glucose_logs[-7:]
        ]

    # ======================================================
    # RECENT ACTIVITY
    # ======================================================

    recent = sorted(
        glucose_logs + carb_logs + insulin_logs,
        key=lambda item: item.recorded_at,
        reverse=True
    )[:8]

        # ======================================================
    # RENDER DASHBOARD
    # ======================================================
    print("Labels:", chart_labels)
    print("Values:", chart_values)
    
    return render_template(
        "dashboard.html",
        user=current_user,

        # Dashboard Statistics
        avg_glucose=avg_glucose,
        total_carbs=total_carbs,
        total_insulin=total_insulin,
        total_logs=total_logs,

        # Weekly Statistics
        weekly_logs=weekly_logs,
        highest_glucose=highest_glucose,
        lowest_glucose=lowest_glucose,
        
        # Today's Statistics
        today_glucose=today_glucose,
        today_carbs=today_carbs,
        today_insulin=today_insulin,

        # Medical Intelligence
        health_score=health_score,
        time_in_range=time_in_range,
        risk=risk,
        trend=trend,
        recommendation=recommendation,
        stability=stability,
        consistency=consistency,
        status_color=status_color,

        # Charts
        chart_labels=chart_labels,
        chart_values=chart_values,

        # Activity
        recent=recent,
        recent_glucose=recent_glucose,
        recent_carbs=recent_carbs,
        recent_insulin=recent_insulin,
    )


# ==========================
# GLUCOSE
# ==========================

# ==========================
# GLUCOSE
# ==========================

@views.route("/glucose", methods=["GET", "POST"])
@login_required
def glucose():

    if request.method == "POST":

        glucose = request.form.get("glucose")

        log = Glucose(
            glucose_level=int(glucose),
            user_id=current_user.id
        )

        db.session.add(log)
        db.session.commit()

        flash("Glucose log added successfully.", "success")

        return redirect(url_for("views.glucose"))

    search = request.args.get("search", "")
    date = request.args.get("date", "")

    query = Glucose.query.filter_by(user_id=current_user.id)

    if search:

        query = query.filter(
            Glucose.glucose_level.like(f"%{search}%")
        )

    if date:

        query = query.filter(
            db.func.date(Glucose.recorded_at) == date
        )

    logs = query.order_by(
        Glucose.recorded_at.desc()
    ).all()

    return render_template(
        "glucose.html",
        logs=logs,
        user=current_user
    )


@views.route("/edit-glucose/<int:id>", methods=["GET","POST"])
@login_required
def edit_glucose(id):

    log = Glucose.query.get_or_404(id)

    if log.user_id != current_user.id:
        return redirect(url_for("views.glucose"))

    if request.method == "POST":

        log.glucose_level = request.form.get("glucose")

        db.session.commit()

        flash("Glucose updated.", "success")

        return redirect(url_for("views.glucose"))

    return render_template(
        "edit_glucose.html",
        log=log,
        user=current_user
    )


@views.route("/delete-glucose/<int:id>")
@login_required
def delete_glucose(id):

    log = Glucose.query.get_or_404(id)

    if log.user_id == current_user.id:

        db.session.delete(log)

        db.session.commit()

        flash("Entry deleted.", "success")

    return redirect(url_for("views.glucose"))

# ==========================
# CARBS
# ==========================

@views.route("/carbs", methods=["GET", "POST"])
@login_required
def carbs():


    if request.method == "POST":

        carbs = request.form.get("grams")

        meal = request.form.get("meal")

        log = Carbs(
            carbs=carbs,
            meal=meal,
            user_id=current_user.id
        )

        db.session.add(log)

        db.session.commit()

        flash("Carbohydrate log saved.", "success")

        return redirect(url_for("views.carbs"))

    logs = (
        Carbs.query.filter_by(user_id=current_user.id)
        .order_by(Carbs.recorded_at.desc())
        .all()
    )

    return render_template(
        "carbs.html",
        logs=logs,
        user=current_user
    )

@views.route("/edit-carb/<int:id>", methods=["GET", "POST"])
@login_required
def edit_carbs(id):

    log = Carbs.query.get_or_404(id)

    if log.user_id != current_user.id:
        return redirect(url_for("views.carbs"))

    if request.method == "POST":

        log.carbs = request.form.get("carbs")
        log.meal = request.form.get("meal")

        db.session.commit()

        flash("Carbohydrate log updated.", "success")

        return redirect(url_for("views.carbs"))

    return render_template(
        "edit_carbs.html",
        log=log,
        user=current_user
    )


@views.route("/delete-carb/<int:id>")
@login_required
def delete_carb(id):

    log = Carbs.query.get_or_404(id)

    if log.user_id == current_user.id:

        db.session.delete(log)

        db.session.commit()

        flash("Carbohydrate log deleted.", "success")

    return redirect(url_for("views.carbs"))


# ==========================
# INSULIN
# ==========================
@views.route("/insulin", methods=["GET", "POST"])
@login_required
def insulin():

    if request.method == "POST":

        units = float(request.form.get("units"))
        insulin_type = request.form.get("type")

        insulin = Insulin(
            units=units,
            insulin_type=insulin_type,
            user_id=current_user.id
        )

        db.session.add(insulin)
        db.session.commit()

        flash("Insulin saved successfully!", "success")

        return redirect(url_for("views.insulin"))

    logs = Insulin.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Insulin.recorded_at.desc()
    ).all()

    return render_template(
        "insulin.html",
        logs=logs,
        user=current_user
    )
@views.route("/edit-insulin/<int:id>", methods=["GET","POST"])
@login_required
def edit_insulin(id):

    log=Insulin.query.get_or_404(id)

    if log.user_id!=current_user.id:
        return redirect(url_for("views.insulin"))

    if request.method=="POST":

        log.units=request.form.get("units")

        log.insulin_type=request.form.get("type")

        db.session.commit()

        flash("Insulin updated.","success")

        return redirect(url_for("views.insulin"))

    return render_template(
        "edit_insulin.html",
        log=log,
        user=current_user
    )


@views.route("/delete-insulin/<int:id>")
@login_required
def delete_insulin(id):

    log = Insulin.query.get_or_404(id)

    if log.user_id == current_user.id:

        db.session.delete(log)

        db.session.commit()

        flash("Insulin log deleted.", "success")

    return redirect(url_for("views.insulin"))


# ==========================
# REPORTS
# ==========================

@views.route("/reports")
@login_required
def reports():

    glucose_logs = (
        Glucose.query.filter_by(user_id=current_user.id)
        .order_by(Glucose.recorded_at.asc())
        .all()
    )

    carb_logs = Carbs.query.filter_by(user_id=current_user.id).all()

    insulin_logs = Insulin.query.filter_by(user_id=current_user.id).all()

    avg_glucose = (
        round(sum(g.glucose_level for g in glucose_logs)/len(glucose_logs))
        if glucose_logs else 0
    )

    total_carbs = sum(c.carbs for c in carb_logs)

    total_insulin = round(
        sum(i.units for i in insulin_logs),
        1
    )

    chart_labels = [
        g.recorded_at.strftime("%b %d")
        for g in glucose_logs
    ]

    chart_values = [
        g.glucose_level
        for g in glucose_logs
    ]

    return render_template(

        "reports.html",

        user=current_user,

        avg_glucose=avg_glucose,

        total_carbs=total_carbs,

        total_insulin=total_insulin,

        chart_labels=chart_labels,

        chart_values=chart_values

    )

# ==========================
# PROFILE
# ==========================

@views.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user
    )
@views.route("/export/pdf")
@login_required
def export_pdf():

    buffer=BytesIO()

    doc=SimpleDocTemplate(buffer)

    styles=getSampleStyleSheet()

    story=[]

    from datetime import datetime

    story.append(Paragraph("DiaTrack", styles["Title"]))
    story.append(Paragraph("<b>Insulin Pump Simulation Report</b>", styles["Heading2"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph(
            f"<b>Patient:</b> {current_user.first_name}",
            styles["Normal"]
            ))

    story.append(Paragraph(
            f"<b>Date Generated:</b> {datetime.now().strftime('%B %d, %Y')}",
            styles["Normal"]
        ))

    story.append(Paragraph("<br/>", styles["Normal"]))

    glucose_logs = Glucose.query.filter_by(user_id=current_user.id).all()
    carb_logs = Carbs.query.filter_by(user_id=current_user.id).all()
    insulin_logs = Insulin.query.filter_by(user_id=current_user.id).all()

    avg_glucose = (
    round(sum(g.glucose_level for g in glucose_logs) / len(glucose_logs))
    if glucose_logs else 0
    )

    total_carbs = sum(c.carbs for c in carb_logs)

    total_insulin = round(
    sum(i.units for i in insulin_logs),
    1
    )

    story.append(Paragraph("<b>Dashboard Summary</b>", styles["Heading2"]))

    story.append(
    Paragraph(
        f"Average Glucose: {avg_glucose} mg/dL",
        styles["Normal"]
    )
    )

    story.append(
    Paragraph(
        f"Total Carbohydrates: {total_carbs} g",
        styles["Normal"]
    )
    )

    story.append(
    Paragraph(
        f"Total Insulin: {total_insulin} Units",
        styles["Normal"]
    )
    )
    # Health Status
    if avg_glucose == 0:
        status = "No Data"
        recommendation = "Start recording your glucose readings."

    elif avg_glucose < 70:
        status = "Low Blood Glucose"
        recommendation = "Eat fast-acting carbohydrates and monitor your glucose."

    elif avg_glucose <= 180:
        status = "Healthy"
        recommendation = "Excellent control. Continue your current routine."

    else:
        status = "High Blood Glucose"
        recommendation = "Monitor your diet and consult your healthcare provider."

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<b>Health Insights</b>", styles["Heading2"]))

    story.append(
    Paragraph(
        f"<b>Health Status:</b> {status}",
        styles["Normal"]
    )
    )

    story.append(
    Paragraph(
        f"<b>Recommendation:</b> {recommendation}",
        styles["Normal"]
    )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<b>Recent Glucose Records</b>", styles["Heading2"]))


    table_data = [["Date", "Time", "Glucose"]]

    for log in glucose_logs[-10:]:
        table_data.append([
            log.recorded_at.strftime("%b %d"),
            log.recorded_at.strftime("%I:%M %p"),
            f"{log.glucose_level} mg/dL"
        ])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
    story.append(table)

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Data_Report.pdf",
        mimetype="application/pdf"
)

@views.route("/export/excel")
@login_required
def export_excel():

    wb=Workbook()

    ws=wb.active

    ws.title = "Dashboard Summary"

    glucose_logs = Glucose.query.filter_by(user_id=current_user.id).all()

    carb_logs = Carbs.query.filter_by(user_id=current_user.id).all()

    insulin_logs = Insulin.query.filter_by(user_id=current_user.id).all()

    avg_glucose = (
    round(sum(g.glucose_level for g in glucose_logs) / len(glucose_logs))
    if glucose_logs else 0
    )

    total_carbs = sum(c.carbs for c in carb_logs)

    total_insulin = round(
    sum(i.units for i in insulin_logs),
    1
    )

    ws.append(["DiaTrack Data Report"])
    ws.append([])

    ws.append(["Patient", current_user.first_name])
    ws.append(["Average Glucose", f"{avg_glucose} mg/dL"])
    ws.append(["Total Carbohydrates", f"{total_carbs} g"])
    ws.append(["Total Insulin", f"{total_insulin} Units"])
    glucose_sheet = wb.create_sheet("Glucose Logs")
    glucose_sheet.append([
    "Date",
    "Time",
    "Glucose (mg/dL)"
])
    for log in glucose_logs:
        glucose_sheet.append([
        log.recorded_at.strftime("%b %d, %Y"),
        log.recorded_at.strftime("%I:%M %p"),
        log.glucose_level
    ])

    output=BytesIO()

    wb.save(output)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Glucose.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
from datetime import date, datetime


@views.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        current_user.first_name = request.form.get("first_name")
        current_user.last_name = request.form.get("last_name")
        current_user.gender = request.form.get("gender")

        birthday = request.form.get("birthday")
        if birthday:
            current_user.birthday = datetime.strptime(
                birthday,
                "%Y-%m-%d"
            ).date()

        db.session.commit()

        flash("Profile updated successfully!", "success")

        return redirect(url_for("views.profile"))

    return render_template(
        "edit_profile.html",
        user=current_user
    )
@views.route("/basal", methods=["GET", "POST"])
@login_required
def basal():

    if request.method == "POST":

        current_user.basal_rate = float(
            request.form.get("basal_rate")
        )

        db.session.commit()

        flash("Basal rate updated successfully.", "success")

        return redirect(url_for("views.basal"))

    return render_template(
        "basal.html",
        user=current_user
    )
@views.route("/bolus", methods=["GET", "POST"])
@login_required
def bolus():

    if request.method == "POST":

        glucose = float(request.form.get("glucose"))
        carbs = float(request.form.get("carbs"))

        # Simple Pump Simulation
        carb_ratio = 15          # 1 unit covers 15g carbs
        target_glucose = 100     # Target BG
        correction_factor = 50   # 1 unit lowers BG by 50 mg/dL

        meal_bolus = carbs / carb_ratio
        correction = max((glucose - target_glucose) / correction_factor, 0)

        recommended = round(meal_bolus + correction, 1)

        return render_template(
            "bolus.html",
            user=current_user,
            recommended=recommended,
            glucose=glucose,
            carbs=carbs
        )

    return render_template(
        "bolus.html",
        user=current_user
    )
@views.route("/edit-avatar", methods=["GET", "POST"])
@login_required
def edit_avatar():

    avatars = [
        "avatar1.png",
        "avatar2.png",
        "avatar3.png",
        "avatar4.png",
        "avatar5.png",
        "avatar6.png",
        "avatar7.png",
        "avatar8.png"
    ]

    if request.method == "POST":

        selected = request.form.get("avatar")

        if selected in avatars:

            current_user.avatar = selected

            db.session.commit()

            flash("Avatar updated successfully!", "success")

            return redirect(url_for("views.profile"))

    return render_template(
        "edit_avatar.html",
        user=current_user,
        avatars=avatars
    )
