from datetime import date, datetime
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Blueprint, render_template, session, jsonify, request, flash, redirect, url_for
from models import UserCrop, CropLog, CropStandard
from extensions import db

crop_tracking_bp = Blueprint("crop_tracking", __name__, template_folder="templates", static_folder="static")

@crop_tracking_bp.route("/crop_tracking")
def crop_tracking():
    if "user_id" not in session:
        flash("Please log in to access Crop Tracking.", "warning")
        return redirect(url_for("login"))
    farms = UserCrop.query.filter_by(user_id=session["user_id"]).all()
    return render_template("Crop_Tracking/crop_tracking.html", farms=farms, today=date.today())

@crop_tracking_bp.route("/api/crop_standards/<int:user_crop_id>")
def crop_standards(user_crop_id):
    user_crop = UserCrop.query.get_or_404(user_crop_id)
    growth_config = user_crop.standard.growth_config or {}
    optimal_lcc = growth_config.get("optimal_lcc", 4)
    stages = growth_config.get("stages", {})
    stage_list = list(stages.items())
    stage_list = sorted(stage_list, key=lambda x: x[1].get("days_start", 0))

    latest_log = CropLog.query.filter(CropLog.user_crop_id == user_crop_id, CropLog.disease_label.isnot(None)).order_by(CropLog.log_date.desc()).first()
    disease_info = None
    if latest_log:
        disease_info = {
            "label": latest_log.disease_label,
            "confidence": round((latest_log.disease_confidence or 0.0) * 100),
            "status": latest_log.disease_status,
            "date": latest_log.log_date.strftime("%b %d, %Y")
        }

    return jsonify({
        "stages": stage_list,
        "optimal_lcc": optimal_lcc,
        "latest_disease": disease_info
    })

@crop_tracking_bp.route("/log_field_data/<int:user_crop_id>", methods=["POST"])
def log_field_data(user_crop_id):
    data = request.get_json() or {}
    if not any(data.values()):
        return jsonify({"alerts": ["No input field data provided"]}), 400

    user_crop = UserCrop.query.get_or_404(user_crop_id)
    crop_log = CropLog.query.filter_by(user_crop_id=user_crop_id, log_date=date.today()).first()

    calc_week = int((date.today() - user_crop.sowing_date).days / 7) + 1
    if calc_week < 1:
        calc_week = 1

    alerts = []
    height_val = float(data["height"]) if data.get("height") else None
    lcc_val = int(data["lcc"]) if data.get("lcc") else None
    moisture_val = data.get("moisture")
    stage_val = data.get("stage")
    stand_val = int(data["stand_count"]) if data.get("stand_count") else None

    # Benchmark Alert Logic (Algorithmic Implementation)
    standard_cfg = user_crop.standard.growth_config or {}
    milestones = standard_cfg.get("height_milestones", {})
    if height_val and milestones:
        expected_h = milestones.get(str(calc_week)) or milestones.get(calc_week)
        if expected_h:
            if height_val < (0.70 * float(expected_h)):
                alerts.append(f"⚠️ Stunted Growth Alert: Plant height ({height_val} cm) is below benchmark ({expected_h} cm). Check soil moisture and nutrients.")
            elif height_val > (1.30 * float(expected_h)):
                alerts.append(f"ℹ️ Rapid/Etiolation Warning: Height ({height_val} cm) exceeds normal benchmark ({expected_h} cm). Ensure adequate sunlight.")

    opt_lcc = standard_cfg.get("optimal_lcc", 4)
    if lcc_val:
        if lcc_val < opt_lcc:
            deficit = opt_lcc - lcc_val
            alerts.append(f"🌱 Nitrogen Deficiency (LCC {lcc_val} vs target {opt_lcc}): Apply approx {deficit * 15} kg Urea/acre.")
        elif lcc_val >= 6:
            alerts.append("⚠️ High Nitrogen (LCC 6): Suspend nitrogen application to prevent pest vulnerability.")

    if not crop_log:
        crop_log = CropLog(
            user_crop_id=user_crop_id,
            log_date=date.today(),
            week_number=calc_week,
            soil_moisture=moisture_val,
            plant_height_cm=height_val,
            lcc_score=lcc_val,
            phenology_stage=stage_val,
            stand_count=stand_val
        )
        db.session.add(crop_log)
    else:
        if moisture_val is not None: crop_log.soil_moisture = moisture_val
        if height_val is not None: crop_log.plant_height_cm = height_val
        if lcc_val is not None: crop_log.lcc_score = lcc_val
        if stage_val is not None: crop_log.phenology_stage = stage_val
        if stand_val is not None: crop_log.stand_count = stand_val

    db.session.commit()
    return jsonify({"alerts": alerts, "message": "Field log saved successfully!"})

@crop_tracking_bp.route("/add_farm", methods=["GET", "POST"])
def add_farm():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        farm_name = request.form.get("farm_name", "").strip()
        crop_id = request.form.get("crop_standard_id")
        sowing_date_str = request.form.get("sowing_date")
        area = request.form.get("area_acres")

        if not all([farm_name, crop_id, sowing_date_str]):
            flash("All farm fields are required.", "warning")
            return redirect(url_for('crop_tracking.add_farm'))

        try:
            new_farm = UserCrop(
                user_id=session.get('user_id'),
                crop_standard_id=int(crop_id),
                farm_name=farm_name,
                sowing_date=datetime.strptime(sowing_date_str, '%Y-%m-%d').date(),
                area_acres=float(area) if area else 1.0,
                status='active'
            )
            db.session.add(new_farm)
            db.session.commit()
            flash(f"Farm '{farm_name}' added successfully!", "success")
            return redirect(url_for('crop_tracking.crop_tracking'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding farm: {str(e)}", "danger")
            return redirect(url_for('crop_tracking.add_farm'))

    all_crops = CropStandard.query.order_by(CropStandard.display_name.asc()).all()
    return render_template("Add_Farm/add_farm.html", crops=all_crops)

@crop_tracking_bp.route("/api/farm_analytics/<int:user_crop_id>")
def farm_analytics(user_crop_id):
    user_crop = UserCrop.query.get_or_404(user_crop_id)
    logs = user_crop.logs
    standard = user_crop.standard.growth_config or {}

    # --- CHART 1: HEIGHT TREND ---
    plt.figure(figsize=(6, 3.8), dpi=100)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    milestones = standard.get('height_milestones', {})
    if milestones:
        expected_weeks = sorted([int(k) for k in milestones.keys()])
        expected_heights = [float(milestones[str(w)]) for w in expected_weeks]
        expected_weeks = [0] + expected_weeks
        expected_heights = [0.0] + expected_heights
        plt.plot(expected_weeks, expected_heights, linestyle='--', color='#27ae60', linewidth=2, label='TNAU/ICAR Benchmark')

    if logs:
        height_logs = [l for l in logs if l.plant_height_cm is not None]
        if height_logs:
            actual_weeks = [l.week_number for l in height_logs]
            actual_heights = [l.plant_height_cm for l in height_logs]
            plt.plot(actual_weeks, actual_heights, marker='o', markersize=6, color='#2980b9', linewidth=2.5, label='Your Farm Data')

    plt.title(f"Plant Height Trajectory: {user_crop.farm_name}", fontsize=11, fontweight='bold', pad=10)
    plt.xlabel("Growth Week", fontsize=10)
    plt.ylabel("Height (cm)", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    height_chart_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    # --- CHART 2: PHENOLOGICAL STAGE DURATION ---
    plt.figure(figsize=(6, 3.8), dpi=100)
    stages_config = standard.get('stages', {})
    sorted_stages = sorted(stages_config.items(), key=lambda x: x[1].get('days_start', 0))

    labels = [s[1].get('label', s[0]) for s in sorted_stages]
    durations = [(s[1].get('days_end', 0) - s[1].get('days_start', 0)) for s in sorted_stages]
    colors = ['#27ae60', '#f39c12', '#7f8c8d', '#e67e22'][:len(labels)]

    bars = plt.bar(labels, durations, color=colors, width=0.55, edgecolor='#333', linewidth=0.5)
    plt.title("Expected Crop Stage Durations", fontsize=11, fontweight='bold', pad=10)
    plt.ylabel("Duration (Days)", fontsize=10)
    plt.grid(axis='y', alpha=0.3)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + 1, f'{int(h)} d', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png', bbox_inches='tight')
    plt.close()
    buf2.seek(0)
    stage_chart_b64 = base64.b64encode(buf2.getvalue()).decode('utf-8')

    return jsonify({
        "height_chart": height_chart_b64,
        "stage_chart": stage_chart_b64
    })
