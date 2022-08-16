# Vaultwarden Kube Backup
This was created as most of the backup solutions I found for Bitwarden ran as a sidecar using cron to run scheduled backups whereas I wanted something I could run as a Kubernetes Cronjob

The container does the following:
- For the files in the directory specified in the  `VW_PATH` environment variable (defaults to /data)
  - Creates an SQLIte backup of db.sqlite3
  - Creates a tar.gz (name is current date and time) of all files in this folder except
    - db.sqlite3
    - db.sqlite3-shm
    - db.sqlite3-wal
- Uploads the created tar.gz to the S3 bucket specified by the `BACKUP_S3_BUCKET` environment variable into the key specifed by the `BACKUP_S3_KEY` environment variable (defaults to Vaultwarden)
- Cleans up the SQLite backup from `VW_PATH`

# Usage
Latest is currently accessible from ghcr.io/jsw1993/vw-backup:latest. CI will be added in the next couple of days

The container takes the following envirnment variables

| Variable Name | Description | Required |  Default |
| --- | --- | --- | --- |
| AWS_ACCESS_KEY_ID | Access key ID to access AWS S3 bucket | N | |
| AWS_SECRET_ACCESS_KEY | Secret access key to access AWS S3 bucket | N | |
| AWS_DEFAULT_REGION | Default region for AWS access | N | |
| BACKUP_S3_BUCKET | Name of S3 Bucket in which to store backup | Y | |
| BACKUP_S3_KEY | S3 Key to store backups under | N | vaultwarden
| VW_PATH | Path to Vaultwarden Data Directory | N | /data |
