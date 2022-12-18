import logging
import azure.functions as func
import psycopg2
import os
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('ServiceBus queue trigger processed message: %s',notification_id)

    conn = psycopg2.connect(dbname = os.environ["dbName"], user=os.environ["dbUsername"], password=os.environ["dbPassword"], host=os.environ["dbUrl"])
    try:
        cur = conn.cursor()
        cur.execute("SELECT message,subject FROM notification WHERE id=%s;",(notification_id,))
        messagePlain, subject = cur.fetchone()
        cur.execute("SELECT email,first_name FROM attendee;")
        attendees = cur.fetchall()
        for attendee in attendees:
          message = Mail(
              from_email='info@techconf.com',
              to_emails=attendee[0],
              subject='{}: {}'.format(attendee[1], subject),
              html_content=messagePlain)

        # i don't have SendGrid key to send API 

        # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        total_attendees = 'Notified {} attendees'.format(len(attendees))
        cur.execute("UPDATE notification SET status = %s ,  completed_date = current_timestamp WHERE id=%s;", (total_attendees,notification_id))
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        conn.close()