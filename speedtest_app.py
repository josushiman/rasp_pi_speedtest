import speedtest
import config
import sqlite3
import logging
from datetime import datetime


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
            download = 999
            upload = 999
            ping = 0
            image_result = "test run"
        self.download = download
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

results = SpeedTest()
insert_to_db(datetime.now(), results.download, results.upload, results.ping, results.image_result)