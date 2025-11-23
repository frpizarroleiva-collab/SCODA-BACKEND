import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def enviar_correo(destinatario, asunto, html):
    """
    Envía un correo usando la API de SendGrid.
    """
    message = Mail(
        from_email=os.getenv("DEFAULT_FROM_EMAIL"),
        to_emails=destinatario,
        subject=asunto,
        html_content=html
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        return {"status": response.status_code, "msg": "Correo enviado correctamente"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
