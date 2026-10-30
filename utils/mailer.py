import logging
from flask_mail import Message
from flask import current_app
from extensions import mail

logger = logging.getLogger(__name__)

def send_otp_email(to_email, otp, full_name):
    mail_user = current_app.config.get("MAIL_USERNAME")
    if not mail_user or not current_app.config.get("MAIL_PASSWORD"):
        logger.warning("OTP email not sent: MAIL_USERNAME and MAIL_PASSWORD must be configured.")
        return False

    try:
        msg = Message(
            subject="Your BioGrow Verification Code 🌱",
            sender=("BioGrow", mail_user),
            recipients=[to_email]
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f4f6f9;font-family:Arial,sans-serif;">
        <table align="center" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:600px;background:white;margin-top:40px;
               border-radius:10px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,0.1);">
            <tr>
                <td style="background:linear-gradient(135deg,#2ecc71,#27ae60);
                           padding:30px;text-align:center;color:white;">
                    <h1 style="margin:0;">🌱 BioGrow</h1>
                    <p style="margin:5px 0 0 0;">Empowering Farmers with Smart Technology</p>
                </td>
            </tr>
            <tr>
                <td style="padding:30px;color:#333;">
                    <h2>Hello {full_name},</h2>
                    <p style="font-size:16px;line-height:1.6;">
                        Welcome to BioGrow 🌾 We're excited to have you in our farmer community.
                    </p>
                    <p style="font-size:16px;">
                        Please use the verification code below:
                    </p>
                    <div style="background:#f1fdf6;
                                border:2px dashed #27ae60;
                                padding:20px;
                                text-align:center;
                                font-size:28px;
                                font-weight:bold;
                                letter-spacing:5px;
                                color:#27ae60;
                                border-radius:8px;
                                margin:20px 0;">
                        {otp}
                    </div>
                    <p style="font-size:14px;color:#777;">
                        ⏳ This OTP is valid for 10 minutes.<br>
                        🔒 Do not share this code with anyone.
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background:#f8f9fa;padding:20px;text-align:center;
                           font-size:12px;color:#888;">
                    © 2026 BioGrow | All Rights Reserved
                </td>
            </tr>
        </table>
        </body>
        </html>
        """

        msg.html = html_content
        mail.send(msg)
        return True
    except Exception:
        logger.exception("Failed to send OTP email to %s", to_email)
        return False
