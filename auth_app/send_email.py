
from django.core.mail import EmailMultiAlternatives

def send_email_ui(
    *,
    subject,
    heading,
    message,
    button_text,
    link,
    from_email,
    recipient_list,
    button_color="#4A90E2",
    icon="✉️",
    footer_message=None,
    logo_url=None,
):
    plain_message = (
        f"{heading}\n\n"
        f"{message}\n\n"
        f"{button_text}: {link}\n\n"
        f"If the button doesn't work, copy and paste this link:\n{link}"
    )

    footer_html = ""
    if footer_message:
        footer_html = f"""
        <tr>
            <td style="padding: 20px 30px; background-color: #f8f9fa; border-top: 1px solid #e9ecef;">
                <p style="margin: 0; font-size: 13px; color: #6c757d; text-align: center; line-height: 1.5;">
                    {footer_message}
                </p>
            </td>
        </tr>
        """

    logo_html = ""
    if logo_url:
        logo_html = f"""
        <tr>
            <td style="padding: 30px 30px 0; text-align: center;">
                <img src="{logo_url}" alt="Logo" style="max-width: 120px; height: auto;">
            </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; -webkit-font-smoothing: antialiased;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    
                    <tr>
                        <td style="background: linear-gradient(135deg, {button_color} 0%, {button_color}dd 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">{icon}</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600; letter-spacing: -0.5px;">
                                {heading}
                            </h1>
                        </td>
                    </tr>

                    {logo_html}

                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 25px; font-size: 16px; line-height: 1.7; color: #495057;">
                                {message}
                            </p>

                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{link}" 
                                           style="display: inline-block; padding: 16px 40px; background-color: {button_color}; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 12px {button_color}40; transition: all 0.3s ease;">
                                            {button_text}
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <table role="presentation" style="width: 100%; background-color: #f8f9fa; border-radius: 8px; margin-top: 25px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 10px; font-size: 13px; color: #6c757d; text-align: center;">
                                            If the button doesn't work, copy and paste this link into your browser:
                                        </p>
                                        <p style="margin: 0; font-size: 13px; color: {button_color}; text-align: center; word-break: break-all; font-family: monospace;">
                                            {link}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    {footer_html}

                    <tr>
                        <td style="padding: 20px; background-color: #f8f9fa; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                                This email was sent from {from_email}
                            </p>
                        </td>
                    </tr>

                </table>
                
                <table role="presentation" style="width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 20px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                                If you didn't expect this email, you can safely ignore it.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=recipient_list,
    )

    email.attach_alternative(html_content, "text/html")
    email.send()