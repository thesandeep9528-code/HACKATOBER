import json
import os
from datetime import date
from flask import Blueprint, render_template, request, jsonify, make_response, session, flash, redirect, url_for
from extensions import db
from models import CropStandard, PredictionReport, UserCrop
from utils.prediction_model import get_prediction, recommend_fertilizer
from utils.water_requirements import crop_water_requirements

crop_prediction_bp = Blueprint("crop_prediction", __name__)

@crop_prediction_bp.route("/crop_prediction")
def crop_prediction():
    return render_template("Crop_Prediction/crop_prediction.html")

@crop_prediction_bp.route("/api/predict-crop", methods=["POST"])
def predict_crop():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        n = float(data.get("n", 0))
        p = float(data.get("p", 0))
        k = float(data.get("k", 0))
        ph = float(data.get("ph", 6.5))
        temp = float(data.get("temp", 25.0))
        humidity = float(data.get("humidity", 60.0))
        soil_type = str(data.get("soil_type", "Alluvial Soil"))

        result, match_percentage = get_prediction(n, p, k, ph, temp, humidity, soil_type)
        recommendations = recommend_fertilizer(result, n, p, k)

        standard = CropStandard.query.filter_by(crop_name=result.lower()).first()
        duration_str = "90 - 120 days"
        duration_list = [90, 120]
        if standard and standard.growth_config:
            total_days = standard.growth_config.get("total_duration_days", [90, 120])
            if isinstance(total_days, list) and len(total_days) >= 2:
                duration_str = f"{total_days[0]} - {total_days[1]} days"
                duration_list = total_days

        water_req = crop_water_requirements.get(result.lower(), "Moderate (450 - 650 mm)")

        user_id = session.get("user_id")
        new_report = PredictionReport(
            user_id=user_id,
            n=n, p=p, k=k,
            ph=ph, humidity=humidity,
            temperature=temp, soil_type=soil_type,
            crop_name=result,
            match_percentage=float(match_percentage),
            water_req=water_req,
            harvest_duration=duration_str,
            recommendations_json=json.dumps(recommendations)
        )

        db.session.add(new_report)
        db.session.commit()

        return jsonify({
            "result": result,
            "match_percentage": match_percentage,
            "recommendations": recommendations,
            "duration": duration_list,
            "water_req": water_req,
            "report_id": new_report.report_id
        })

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": "Invalid numeric format for N, P, K, pH, Temperature or Humidity."}), 400
    except Exception as e:
        return jsonify({"error": f"Prediction computation failed: {str(e)}"}), 500


def generate_pdf_from_report(rendered_html, report, data_for_pdf):
    # Tier 1: Try xhtml2pdf (pure Python, fast, no external binary required)
    try:
        from xhtml2pdf import pisa
        import io
        pdf_io = io.BytesIO()
        status = pisa.CreatePDF(rendered_html, dest=pdf_io)
        if not status.err and len(pdf_io.getvalue()) > 0:
            return pdf_io.getvalue()
    except Exception as e:
        print(f"[BioGrow PDF] xhtml2pdf generation notice: {e}")

    # Tier 2: Try pdfkit if wkhtmltopdf is configured on system
    try:
        import pdfkit
        wkhtml_path = os.getenv("PATH_WKHTMLTOPDF")
        config = pdfkit.configuration(wkhtmltopdf=wkhtml_path) if wkhtml_path else None
        pdf = pdfkit.from_string(rendered_html, False, configuration=config)
        if pdf:
            return pdf
    except Exception as e:
        print(f"[BioGrow PDF] pdfkit generation notice: {e}")

    # Tier 3: Pure ReportLab failsafe
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setTitle(f"BioGrow Report - {report.crop_name.capitalize()}")
        c.setFont("Helvetica-Bold", 18)
        c.setFillColorRGB(0.098, 0.529, 0.329)
        c.drawString(50, 750, "BioGrow Crop Recommendation Report")
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(50, 730, f"Generated: {data_for_pdf['report_date']} | Report ID: #{report.report_id}")
        c.setStrokeColorRGB(0.098, 0.529, 0.329)
        c.setLineWidth(2)
        c.line(50, 720, 550, 720)

        c.setFont("Helvetica-Bold", 13)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(50, 690, f"Top Recommended Crop: {report.crop_name.capitalize()}")
        c.setFont("Helvetica", 11)
        c.drawString(60, 670, f"Confidence Match: {report.match_percentage}%")
        c.drawString(60, 650, f"Estimated Harvest: {report.harvest_duration} days")
        c.drawString(60, 630, f"Seasonal Water Requirement: {report.water_req} mm")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 595, "Soil & Climate Profile:")
        c.setFont("Helvetica", 10)
        y = 575
        for k, v in [
            ("Soil Type", report.soil_type),
            ("Nitrogen (N)", f"{report.n} kg/ha"),
            ("Phosphorus (P)", f"{report.p} kg/ha"),
            ("Potassium (K)", f"{report.k} kg/ha"),
            ("pH Level", str(report.ph)),
            ("Temperature", f"{report.temperature} °C"),
            ("Humidity", f"{report.humidity} %"),
        ]:
            c.drawString(60, y, f"• {k}: {v}")
            y -= 18

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 10, "Fertilizer & Action Plan:")
        y -= 30
        for rec in data_for_pdf["result"]["recommendations"]:
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"• {rec}")
            y -= 18

        c.save()
        return buffer.getvalue()
    except Exception as e:
        print(f"[BioGrow PDF] ReportLab fallback notice: {e}")
        return None


@crop_prediction_bp.route('/download_report/<int:report_id>', methods=['GET'])
def download_report(report_id):
    report = PredictionReport.query.get_or_404(report_id)

    if session.get("user_id") and report.user_id and report.user_id != session.get("user_id"):
        return jsonify({"error": "Unauthorized access to report."}), 403

    try:
        recs = json.loads(report.recommendations_json) if report.recommendations_json else []
    except Exception:
        recs = []

    data_for_pdf = {
        "report_date": report.created_at.strftime("%Y-%m-%d %H:%M"),
        "report_id": report.report_id,
        "current_year": report.created_at.year,
        "inputs": {
             "n": report.n, "p": report.p, "k": report.k,
             "ph": report.ph, "temp": report.temperature,
             "humidity": report.humidity, "soil_type": report.soil_type
        },
        "result": {
            "crop_name": report.crop_name,
            "match_percentage": report.match_percentage,
            "water_requirement": report.water_req,
            "harvest_duration": report.harvest_duration,
            "recommendations": recs
        }
    }

    rendered_html = render_template('pdf_report.html', **data_for_pdf)

    pdf_bytes = generate_pdf_from_report(rendered_html, report, data_for_pdf)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        safe_crop = "".join([c for c in report.crop_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        response.headers['Content-Disposition'] = f'attachment; filename="BioGrow_{safe_crop.capitalize()}_Report.pdf"'
        return response

    return rendered_html

@crop_prediction_bp.route("/api/create_farm_from_prediction", methods=["POST"])
def create_farm_from_prediction():
    if "user_id" not in session:
        return jsonify({"error": "Please log in to add this crop to your farms."}), 401

    data = request.get_json() or {}
    crop_name = data.get("crop_name", "").strip().lower()
    farm_name = data.get("farm_name", "").strip() or f"My {data.get('crop_name', 'Crop').capitalize()} Field"
    area_acres = float(data.get("area_acres", 1.0))

    if not crop_name:
        return jsonify({"error": "Crop name is required."}), 400

    standard = CropStandard.query.filter(CropStandard.crop_name.ilike(f"%{crop_name}%")).first()
    if not standard:
        standard = CropStandard.query.filter(CropStandard.display_name.ilike(f"%{crop_name}%")).first()

    if not standard:
        standard = CropStandard(
            crop_name=crop_name,
            display_name=crop_name.capitalize(),
            category="Cereals & Pulses",
            growth_config={
                "total_duration_days": [90, 120],
                "optimal_lcc": 4,
                "stages": {
                    "Vegetative": {"days_start": 0, "days_end": 35},
                    "Flowering": {"days_start": 36, "days_end": 70},
                    "Maturity": {"days_start": 71, "days_end": 110}
                }
            }
        )
        db.session.add(standard)
        db.session.commit()

    new_user_crop = UserCrop(
        user_id=session["user_id"],
        crop_standard_id=standard.crop_standard_id,
        farm_name=farm_name,
        sowing_date=date.today(),
        area_acres=area_acres,
        status="active"
    )
    db.session.add(new_user_crop)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully added '{standard.display_name}' ({farm_name}) to your tracked farms!",
        "user_crop_id": new_user_crop.user_crop_id,
        "redirect_url": url_for("crop_tracking.crop_tracking")
    })
