#!/usr/bin/env python3
"""
QuakeFlow Configuration Setup Script
設定ファイルとパラメータを生成するスクリプト
"""

import datetime
import json
import os
import pickle
import numpy as np
import obspy

def main():
    # 環境変数から設定を取得
    region_name = os.environ.get('REGION_NAME', 'Ridgecrest')
    num_parallel = int(os.environ.get('NUM_PARALLEL', '1'))
    bucket_name = os.environ.get('BUCKET_NAME', 'catalogs')
    s3_url = os.environ.get('S3_URL', 'minio-service:9000')
    secure = os.environ.get('SECURE', 'false').lower() == 'true'
    
    degree2km = np.pi * 6371 / 180

    # 地域別設定
    if region_name == "Demo":
        center = (-117.504, 35.705)
        horizontal_degree = 1.0
        vertical_degree = 1.0
        starttime = obspy.UTCDateTime("2019-07-04T17")
        endtime = obspy.UTCDateTime("2019-07-04T19")
        client = "SCEDC"
        network_list = ["CI"]
        channel_list = "HH*,BH*,EH*,HN*"

    elif region_name == "Ridgecrest":
        center = (-117.504, 35.705)
        horizontal_degree = 1.0
        vertical_degree = 1.0
        starttime = obspy.UTCDateTime("2019-07-04T00")
        endtime = obspy.UTCDateTime("2019-07-10T00")
        client = "SCEDC"
        network_list = ["CI"]
        channel_list = "HH*,BH*,EH*,HN*"

    elif region_name == "Japan":
        # 日本の設定例
        center = (138.0, 36.0)
        horizontal_degree = 10.0
        vertical_degree = 8.0
        starttime = obspy.UTCDateTime("2024-01-01T00")
        endtime = obspy.UTCDateTime("2024-01-31T00")
        client = "NIED"  # 防災科研
        network_list = ["N.NIED"]
        channel_list = "HH*,BH*,EH*"

    else:
        # デフォルト設定
        center = (-117.504, 35.705)
        horizontal_degree = 1.0
        vertical_degree = 1.0
        starttime = obspy.UTCDateTime("2019-07-04T00")
        endtime = obspy.UTCDateTime("2019-07-10T00")
        client = "SCEDC"
        network_list = ["CI"]
        channel_list = "HH*,BH*,EH*,HN*"

    # 設定辞書を作成
    config = {
        "region": region_name,
        "center": center,
        "xlim_degree": [
            center[0] - horizontal_degree / 2,
            center[0] + horizontal_degree / 2,
        ],
        "ylim_degree": [
            center[1] - vertical_degree / 2,
            center[1] + vertical_degree / 2,
        ],
        "min_longitude": center[0] - horizontal_degree / 2,
        "max_longitude": center[0] + horizontal_degree / 2,
        "min_latitude": center[1] - vertical_degree / 2,
        "max_latitude": center[1] + vertical_degree / 2,
        "degree2km": degree2km,
        "starttime": starttime.datetime.isoformat(timespec="milliseconds"),
        "endtime": endtime.datetime.isoformat(timespec="milliseconds"),
        "networks": network_list,
        "channels": channel_list,
        "client": client,
        "phasenet": {},
        "gamma": {},
        "hypodd": {"MAXEVENT": 1e4}
    }

    # 設定ファイルを保存
    with open("config.json", "w") as fp:
        json.dump(config, fp, indent=2)

    print(f"Configuration created for region: {region_name}")
    print(json.dumps(config, indent=2))

    # 並列処理用のインデックスを作成
    one_hour = datetime.timedelta(hours=1)
    starttimes = []
    tmp_start = starttime
    while tmp_start < endtime:
        starttimes.append(tmp_start.datetime.isoformat(timespec="milliseconds"))
        tmp_start += one_hour

    # 日時情報を保存
    with open("datetime.json", "w") as fp:
        json.dump(
            {"starttimes": starttimes, "interval": one_hour.total_seconds()},
            fp,
            indent=2,
        )

    # 並列処理のインデックスを作成
    if num_parallel == 0:
        num_parallel = min(60, int((len(starttimes) - 1) // 6 + 1))
    
    idx = [x.tolist() for x in np.array_split(np.arange(len(starttimes)), num_parallel)]

    with open("index.json", "w") as fp:
        json.dump(idx, fp, indent=2)

    # MinIOにアップロード（オプション）
    try:
        from minio import Minio
        minioClient = Minio(s3_url, access_key="minio", secret_key="minio123", secure=secure)
        if not minioClient.bucket_exists(bucket_name):
            minioClient.make_bucket(bucket_name)

        minioClient.fput_object(bucket_name, f"{config['region']}/config.json", "config.json")
        minioClient.fput_object(bucket_name, f"{config['region']}/datetime.json", "datetime.json")
        minioClient.fput_object(bucket_name, f"{config['region']}/index.json", "index.json")
        
        print(f"Files uploaded to MinIO bucket: {bucket_name}")
    except Exception as err:
        print(f"WARNING: Could not upload to MinIO: {err}")

    print(f"Configuration setup completed for {region_name}")
    return list(range(num_parallel))

if __name__ == "__main__":
    main() 