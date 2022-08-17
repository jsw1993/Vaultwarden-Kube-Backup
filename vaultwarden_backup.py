"""Script to create backup of Vaultwarden. Designed to run as a Kubernetes cronJob"""
from asyncio.log import logger
import sqlite3
import tarfile
import logging
import os
import sys
from datetime import datetime
import boto3
import botocore

def progress(status, remaining, total):
    """Used to display progress of SQLite Backup"""
    del status
    current = total-remaining
    logging.debug('Copied %d of %d pages...', current, total)

def checksqlitefiles():
    """Used to check the VW_PATH is a Bitwarden path and contains db.sqlite3"""
    logging.debug("Starting to check VaultWadrden directory")
    try:
        sqlitefiles = [_ for _ in os.listdir(datapath) if _.endswith(".sqlite3")]
    except os.error as error:
        logger.error("Error getting files in datapath: %d", error)
        return 1
    if len(sqlitefiles) > 1:
        logging.warning(
            "More than one sqlite file in data folder. This will mean a larger backup"
            )
    if len(sqlitefiles) == 1:
        logging.info("One SQLite File found. This is expected behaviour")
    if "db.sqlite3" not in sqlitefiles:
        logging.error("db.sqlite3 file not present. Are you sure this is a VaultWarden directory?")
        return 1
    return 0

def runsqlitebackup():
    """Creates backup of db.sqlite3 in VW_PATH"""
    sqlitefile= datapath+"/db.sqlite3"
    dbbackup= datapath+"/db-"+timestamp+"-bak.sqlite3"
    try:
        sqlitecon = sqlite3.connect(sqlitefile)
        backupcon = sqlite3.connect(dbbackup)
        with backupcon:
            sqlitecon.backup(backupcon, pages=3, progress=progress)
            logging.info("SQLite backup successful")
    except sqlite3.Error as error:
        logging.error("Error while taking SQLite backup: %d", error)
        return 1
    finally:
        if backupcon:
            backupcon.close()
            sqlitecon.close()
    return 0

def compressbackup():
    '''Creates tar containing backup files excluding the live database'''
    try:
        tar = tarfile.open(timestamp+".tar.gz", "w:gz")
        with tar:
            logging.debug("Tar created sucesfully")
            tar.add(datapath, arcname=os.path.basename(datapath), filter=filter_function)
            logging.info("Files added to tar")
            tar.close()
            return 0
    except tarfile.TarError as error:
        logging.error("Error while creating tar.gz: %d", error)
        return 1

def filter_function(tarinfo):
    '''Filter function used to exclude live SQLite database files'''
    exclude_files = ['db.sqlite3', 'db.sqlite3-shm', 'db.sqlite3-wal']
    if os.path.basename(tarinfo.name) in exclude_files:
        return None

    return tarinfo

def uploadtar():
    '''Uploads created tar to s3'''
    try:
        s3_client = boto3.client("s3")
        s3_client.upload_file(
            Filename=timestamp+".tar.gz",
            Bucket=s3bucket,
            Key=s3key+"/"+timestamp+".tar.gz",
        )
        logging.info("S3 Backup Sucessful")
        return 0

    except botocore.exceptions.ClientError as error:
        logging.error("Error uploading to S3: %d", error)
        return 1


def cleanup():
    '''Cleans up old SQLite backups'''
    try:
        datadir = os.listdir(datapath)
        for file in datadir:
            if file.endswith("-bak.sqlite3"):
                logging.info("Removing %s", file)
                os.remove(datapath+"/"+file)
        return 0
    except os.error as error:
        logging.error('Error cleaning up: %d', error)
        return 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

datapath = os.getenv("VW_PATH", "/data")
if os.environ.get('BACKUP_S3_BUCKET') is None:
    logging.critical("BACKUP_S3_BUCKET is not set")
    sys.exit("BACKUP_S3_BUCKET is not set")

s3bucket = os.environ.get('BACKUP_S3_BUCKET')
s3key = os.getenv("BACKUP_S3_KEY", "vaultwarden")


if checksqlitefiles() == 1:
    logging.critical("VaultWarden Backup Failed")
    sys.exit("Error checking VaultWarden Files")
if runsqlitebackup() == 1:
    logging.critical("VaultWarden Backup Failed")
    sys.exit("Error creating SQLite Backup")
if compressbackup() == 1:
    logging.critical("VaultWarden Backup Failed")
    sys.exit("Error creating backup tar")
if uploadtar() == 1:
    logging.critical("VaultWarden Backup Failed")
    sys.exit("Error uploading to S3")
if cleanup() == 1:
    logging.error("Backup was suecessful but cleanup failed")

logging.info("VaultWarden Backup Sucessful")
