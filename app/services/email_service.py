"""Email service for sending transactional emails."""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    @staticmethod
    def send_email(
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional, will strip HTML if not provided)
            from_name: Override default from name
            reply_to: Reply-to email address
            
        Returns:
            True if email sent successfully, False otherwise
        """
        settings = get_settings()
        
        if not settings.smtp_enabled:
            logger.info(f"[EMAIL DEV MODE] Would send email to: {to}")
            logger.info(f"[EMAIL DEV MODE] Subject: {subject}")
            logger.info(f"[EMAIL DEV MODE] HTML Body:\n{html_body[:500]}...")
            if text_body:
                logger.info(f"[EMAIL DEV MODE] Text Body:\n{text_body}")
            return True
        
        if not settings.smtp_host or not settings.smtp_user:
            logger.error("SMTP not configured. Set SMTP_HOST and SMTP_USER in .env")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name or settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg['To'] = to
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            
            msg.attach(MIMEText(html_body, 'html'))
            
            if settings.smtp_use_tls:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    @staticmethod
    def get_password_reset_template(
        user_name: str,
        reset_url: str,
        studio_name: str,
        studio_logo_url: Optional[str] = None,
        brand_color: str = "#0a58d0",
        expiry_hours: int = 1
    ) -> Tuple[str, str]:
        """
        Generate password reset email template.
        
        Returns:
            Tuple of (html_body, text_body)
        """
        # Only include logo if it's a valid external URL (not localhost or relative path)
        logo_html = ""
        if studio_logo_url and studio_logo_url.startswith(('https://', 'http://')) and 'localhost' not in studio_logo_url:
            logo_html = f'<img src="{studio_logo_url}" alt="{studio_name}" style="max-width: 150px; max-height: 60px; margin-bottom: 10px;">'
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset your password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-height: 100vh;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);">
                    <!-- Header with Logo -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px 40px;">
                            {logo_html}
                            <p style="margin: 0; font-size: 18px; font-weight: 600; color: #333333;">{studio_name}</p>
                        </td>
                    </tr>
                    
                    <!-- Password Icon -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <div style="width: 70px; height: 70px; background-color: {brand_color}; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                                <span style="color: #ffffff; font-size: 24px; font-weight: bold;">*****</span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Title -->
                    <tr>
                        <td align="center" style="padding: 10px 40px;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #333333;">Reset your password</h1>
                        </td>
                    </tr>
                    
                    <!-- Message -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <p style="margin: 0; font-size: 16px; line-height: 1.6; color: #666666;">
                                Hey {user_name}, a request has been received to change the password for your {studio_name} account.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td align="center" style="padding: 30px 40px;">
                            <a href="{reset_url}" style="display: inline-block; padding: 14px 40px; background-color: #1a1a1a; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 500; border-radius: 6px;">Reset Password</a>
                        </td>
                    </tr>
                    
                    <!-- Expiry Notice -->
                    <tr>
                        <td align="center" style="padding: 0 40px 20px 40px;">
                            <p style="margin: 0; font-size: 14px; color: #999999;">
                                This link expires in {expiry_hours} hour{'s' if expiry_hours > 1 else ''}.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Fallback Link -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <p style="margin: 0; font-size: 14px; color: #666666;">
                                If the link didn't work, paste this link to your browser:
                            </p>
                            <p style="margin: 10px 0 0 0; font-size: 14px; word-break: break-all;">
                                <a href="{reset_url}" style="color: {brand_color};">{reset_url}</a>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Security Notice -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <p style="margin: 0; font-size: 14px; color: #666666;">
                                If you didn't request a password change, simply ignore this email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Divider -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 0;">
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 40px 40px;">
                            <p style="margin: 0; font-size: 14px; color: #666666;">Thank you,</p>
                            <p style="margin: 5px 0 0 0; font-size: 16px; font-style: italic; color: #333333;">{studio_name} Team</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        text_body = f"""
Reset your password

Hey {user_name}, a request has been received to change the password for your {studio_name} account.

Click the link below to reset your password:
{reset_url}

This link expires in {expiry_hours} hour{'s' if expiry_hours > 1 else ''}.

If you didn't request a password change, simply ignore this email.

Thank you,
{studio_name} Team
"""
        
        return html_body.strip(), text_body.strip()
    
    @staticmethod
    def send_password_reset_email(
        to: str,
        user_name: str,
        reset_url: str,
        studio_name: str,
        studio_logo_url: Optional[str] = None,
        brand_color: str = "#0a58d0",
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send a password reset email with tenant branding.
        
        Args:
            to: Recipient email address
            user_name: User's display name
            reset_url: Full password reset URL with token
            studio_name: Studio/tenant name for branding
            studio_logo_url: URL to studio logo (optional)
            brand_color: Brand color for button (default: blue)
            reply_to: Reply-to email address (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        settings = get_settings()
        
        html_body, text_body = EmailService.get_password_reset_template(
            user_name=user_name,
            reset_url=reset_url,
            studio_name=studio_name,
            studio_logo_url=studio_logo_url,
            brand_color=brand_color,
            expiry_hours=settings.password_reset_expiry_hours
        )
        
        return EmailService.send_email(
            to=to,
            subject=f"Reset your password - {studio_name}",
            html_body=html_body,
            text_body=text_body,
            from_name=studio_name,
            reply_to=reply_to
        )
