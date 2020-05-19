import speedtest
import config
import sqlite3
import logging
import math
import smtplib
from datetime import datetime
from email.message import EmailMessage


# Fetching config params, all are Boolean values to dictate their run mode.
REAL_RUN = config.run_mode["real_run"]
DOWNLOAD = config.run_mode["download"]
UPLOAD = config.run_mode["upload"]
IMAGE = config.run_mode["image"]

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

log_file_handler = logging.FileHandler('speedtest_app.log')
log_file_handler.setFormatter(log_formatter)

logger.addHandler(log_file_handler)

class SpeedTest:
    def __init__(self):
        logger.debug(f"Initialising SpeedTest Object")
        if REAL_RUN:
            logger.debug("Getting stats from Ookla Speedtest")
            results_dict = get_stats()
            logger.info("Successfully retrieved results from Speedtest")
            logger.debug(f"Results output from Speedtest: {results_dict}")
            download = results_dict["download"]
            upload = results_dict["upload"]
            ping = results_dict["ping"]
            image_result = results_dict["share"]
        else:
            logger.debug("Dry run initiated")
            download = 92940235.48505305
            upload = 9411432.82589555
            ping = 23.088
            image_result = "test run"
        self.download = download
        self.download_threshold = config.thresholds["download"]
        self.upload = upload
        self.ping = ping
        self.image_result = image_result
        logger.info(f"Successfully initialised SpeedTest Object")
        
def get_stats():
    servers = []
    # If you want to test against a specific server
    # servers = [1234]

    threads = None
    # If you want to use a single threaded test
    # threads = 1
    try:
        s = speedtest.Speedtest()
        s.get_servers(servers)
        s.get_best_server()
        s.download(threads=threads)
        s.upload(threads=threads)
        s.results.share()
    except Exception as e:
        logger.exception(f"Exception raised: {e}")
    
    return s.results.dict()

def insert_to_db(date, download, upload, ping, image_result):
    db = sqlite3.connect('speedtest_results.db')
    c = db.cursor()
    c.execute ('''CREATE TABLE IF NOT EXISTS results (
      id integer primary key, 
      date text, 
      download integer, 
      upload integer, 
      ping integer,
      image_result text
    );''')
    try:
        sql_insert = f"INSERT INTO results (date, download, upload, ping, image_result) VALUES ('{date}', {download}, {upload}, {ping}, '{image_result}');"
        logger.debug(f"Attempting to INSERT to DB: {sql_insert}")
        c.execute(sql_insert)
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.exception(f"Exception raised: {e}")
    finally:
        logger.debug(f"INSERT to DB SUCCESSFUL")
        db.close()

def convert_size(size_bytes, suffix):
    '''
    Converts bytes to its prettier version e.g. KB/MB per second

    integer : size_bytes
    '''
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    if suffix:
        return f"{s} {size_name[i]}/s"
    return s

def send_email():
    # Retrieving config for Gmail
    EMAIL_ADDRESS = config.gmail["sender_email"]
    EMAIL_PASSWORD = config.gmail["sender_password"]
    EMAIL_RECIPIENT = config.gmail["recipient_email"]

    msg = EmailMessage()
    msg['Subject'] = 'Speedtest Results'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_RECIPIENT

    msg.set_content(f"Download: {convert_size(results.download, True)} should be: {results.download_threshold}\nUpload: {convert_size(results.upload, True)}\nPing: {results.ping} ms")

    if REAL_RUN:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    else:
        # Run this command in terminal before running the app to run a debug server on your local to see these messages.
        # python3 -m smtpd -c DebuggingServer -n localhost:1025
        with smtplib.SMTP('localhost', 1025) as smtp:
            smtp.send_message(msg)

results = SpeedTest()
insert_to_db(datetime.now(), convert_size(results.download, False), convert_size(results.upload, False), results.ping, results.image_result)

if convert_size(results.download, False) <= results.download_threshold:
    logger.warning(f"Download Threshold hit. Current Download:{convert_size(results.download, False)}, Threshold: {results.download_threshold}")
    logger.info("Sending email notification")
    send_email()
    logger.info("Email notification successfully sent")
else:
    logger.info("Download Threshold not hit")