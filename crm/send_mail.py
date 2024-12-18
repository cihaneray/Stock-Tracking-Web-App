import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


def send_new_password(recipient_email, new_password):
    message = MIMEMultipart('alternative')
    message['Subject'] = 'Yeni Geçici Şife.'
    sender_name = '' # Write sender name
    sender_email = '' # Write sender email
    message['From'] = formataddr((sender_name, sender_email))

    message['To'] = recipient_email

    text = 'Yeni Geçici Şifre.'
    html = f"""\
    <html>
    <head></head>
    <body>
        <p>Yeni geçici kullanıcı şifeniz: <b style="color: green;">{new_password}</b> Giriş yaptıktan sonra şifenizi
         güvenliğiniz için değiştiriniz.</p>
    </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    message.attach(part1)  # text must be the first one
    message.attach(part2)  # html must be the last one

    email_server = smtplib.SMTP("mail-server", 587) # Write mail smtp server instead of mail-server 
    email_server.starttls()
    email_server.login(sender_email, "password") # Write password instead of password
    email_server.sendmail(sender_email, recipient_email, message.as_string())
    email_server.quit()
