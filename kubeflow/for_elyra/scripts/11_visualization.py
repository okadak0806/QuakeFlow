#!/usr/bin/env python3
"""
QuakeFlow Visualization Script
解析結果を可視化するスクリプト
"""

import json
import os
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import plotly.graph_objects as go

matplotlib.use("agg")

def plot3d(x, y, z, config, fig_name, title=""):
    """3Dプロットを作成"""
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="markers",
                marker=dict(
                    size=3.0, 
                    color=-z, 
                    cmin=-60, 
                    cmax=2, 
                    colorscale="Viridis", 
                    opacity=0.8
                ),
            )
        ],
    )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(nticks=4, range=config["xlim_degree"]),
            yaxis=dict(nticks=4, range=config["ylim_degree"]),
            zaxis=dict(nticks=4, range=[60, -2]),
            aspectratio=dict(x=1, y=1, z=0.5),
        ),
        margin=dict(r=0, l=0, b=0, t=40),
    )
    fig.write_html(fig_name)

def main():
    # 環境変数から設定を取得
    bucket_name = os.environ.get('BUCKET_NAME', 'catalogs')
    s3_url = os.environ.get('S3_URL', 'minio-service:9000')
    secure = os.environ.get('SECURE', 'false').lower() == 'true'

    # 設定ファイルを読み込み
    with open("config.json", "r") as fp:
        config = json.load(fp)

    print(f"Creating visualizations for region: {config['region']}")

    # 結果ファイルを読み込み
    try:
        # HypoDD結果
        hypodd_ct_catalog = pd.read_csv(
            "hypodd.reloc",
            sep=r"\s+",
            names=[
                "ID", "LAT", "LON", "DEPTH", "X", "Y", "Z", "EX", "EY", "EZ",
                "YR", "MO", "DY", "HR", "MI", "SC", "MAG", "NCCP", "NCCS",
                "NCTP", "NCTS", "RCC", "RCT", "CID",
            ],
        )
        hypodd_ct_catalog["time"] = hypodd_ct_catalog.apply(
            lambda x: f'{x["YR"]:04.0f}-{x["MO"]:02.0f}-{x["DY"]:02.0f}T{x["HR"]:02.0f}:{x["MI"]:02.0f}:{min(x["SC"], 59.999):05.3f}',
            axis=1,
        )
        hypodd_ct_catalog["magnitude"] = hypodd_ct_catalog["MAG"]
        hypodd_ct_catalog["time"] = hypodd_ct_catalog["time"].apply(
            lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f")
        )
        print(f"Loaded {len(hypodd_ct_catalog)} HypoDD events")
    except FileNotFoundError:
        print("WARNING: HypoDD results not found")
        hypodd_ct_catalog = pd.DataFrame()

    try:
        # GaMMA結果
        gamma_catalog = pd.read_csv("gamma_catalog.csv", parse_dates=["time"])
        gamma_catalog["depth_km"] = gamma_catalog["depth(m)"] / 1e3
        print(f"Loaded {len(gamma_catalog)} GaMMA events")
    except FileNotFoundError:
        print("WARNING: GaMMA results not found")
        gamma_catalog = pd.DataFrame()

    try:
        # 標準カタログ
        standard_catalog = pd.read_csv("standard_catalog.csv", parse_dates=["time"])
        standard_catalog["depth_km"] = standard_catalog["depth(m)"] / 1e3
        print(f"Loaded {len(standard_catalog)} standard catalog events")
    except FileNotFoundError:
        print("WARNING: Standard catalog not found")
        standard_catalog = pd.DataFrame()

    # 3Dプロットを作成
    if not hypodd_ct_catalog.empty:
        plot3d(
            hypodd_ct_catalog["LON"],
            hypodd_ct_catalog["LAT"],
            hypodd_ct_catalog["DEPTH"],
            config,
            "hypodd_ct_catalog.html",
            f"HypoDD Catalog - {config['region']} ({len(hypodd_ct_catalog)} events)"
        )

    if not gamma_catalog.empty:
        plot3d(
            gamma_catalog["longitude"],
            gamma_catalog["latitude"],
            gamma_catalog["depth_km"],
            config,
            "gamma_catalog.html",
            f"GaMMA Catalog - {config['region']} ({len(gamma_catalog)} events)"
        )

    if not standard_catalog.empty:
        plot3d(
            standard_catalog["longitude"],
            standard_catalog["latitude"],
            standard_catalog["depth_km"],
            config,
            "standard_catalog.html",
            f"Standard Catalog - {config['region']} ({len(standard_catalog)} events)"
        )

    # 時系列ヒストグラム
    bins = 30
    config["starttime"] = datetime.fromisoformat(config["starttime"])
    config["endtime"] = datetime.fromisoformat(config["endtime"])

    fig, ax = plt.subplots(figsize=(12, 6))
    
    if not gamma_catalog.empty:
        ax.hist(
            gamma_catalog["time"], 
            range=(config["starttime"], config["endtime"]), 
            bins=bins, 
            edgecolor="k", 
            alpha=1.0, 
            linewidth=0.5, 
            label=f"GaMMA: {len(gamma_catalog)}"
        )
    
    if not hypodd_ct_catalog.empty:
        ax.hist(
            hypodd_ct_catalog["time"], 
            range=(config["starttime"], config["endtime"]), 
            bins=bins, 
            edgecolor="k", 
            alpha=0.8, 
            linewidth=0.5, 
            label=f"HypoDD: {len(hypodd_ct_catalog)}"
        )
    
    if not standard_catalog.empty:
        ax.hist(
            standard_catalog["time"], 
            range=(config["starttime"], config["endtime"]), 
            bins=bins, 
            edgecolor="k", 
            alpha=0.6, 
            linewidth=0.5, 
            label=f"Standard: {len(standard_catalog)}"
        )

    ax.set_ylabel("Frequency")
    ax.autoscale(enable=True, axis='x', tight=True)
    fig.autofmt_xdate()
    ax.legend()
    ax.set_title(f"Earthquake Frequency vs Time - {config['region']}")
    fig.savefig("earthquake_frequency_time.png", bbox_inches="tight", dpi=300)
    plt.close()

    # マグニチュード頻度分布
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # マグニチュード範囲を決定
    all_mags = []
    if not gamma_catalog.empty:
        all_mags.extend(gamma_catalog["magnitude"].dropna())
    if not hypodd_ct_catalog.empty:
        all_mags.extend(hypodd_ct_catalog["magnitude"].dropna())
    if not standard_catalog.empty:
        all_mags.extend(standard_catalog["magnitude"].dropna())
    
    if all_mags:
        xrange = (-1.0, max(all_mags) + 0.5)
        
        if not gamma_catalog.empty:
            ax.hist(
                gamma_catalog["magnitude"].dropna(), 
                range=xrange, 
                bins=bins, 
                alpha=1.0, 
                edgecolor="k", 
                linewidth=0.5, 
                label=f"GaMMA: {len(gamma_catalog['magnitude'].dropna())}"
            )
        
        if not hypodd_ct_catalog.empty:
            ax.hist(
                hypodd_ct_catalog["magnitude"].dropna(), 
                range=xrange, 
                bins=bins, 
                alpha=0.6, 
                edgecolor="k", 
                linewidth=0.5, 
                label=f"HypoDD: {len(hypodd_ct_catalog['magnitude'].dropna())}"
            )
        
        if not standard_catalog.empty:
            ax.hist(
                standard_catalog["magnitude"].dropna(), 
                range=xrange, 
                bins=bins, 
                alpha=0.6, 
                edgecolor="k", 
                linewidth=0.5, 
                label=f"Standard: {len(standard_catalog['magnitude'].dropna())}"
            )

    ax.legend()
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Frequency")
    ax.set_yscale('log')
    ax.set_title(f"Magnitude Frequency Distribution - {config['region']}")
    fig.savefig("earthquake_magnitude_frequency.png", bbox_inches="tight", dpi=300)
    plt.close()

    # マグニチュード時系列
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if not gamma_catalog.empty:
        ax.plot(
            gamma_catalog["time"], 
            gamma_catalog["magnitude"], 
            '.', 
            markersize=5.0, 
            alpha=1.0, 
            rasterized=True, 
            label=f"GaMMA: {len(gamma_catalog['magnitude'].dropna())}"
        )
    
    if not hypodd_ct_catalog.empty:
        ax.plot(
            hypodd_ct_catalog["time"], 
            hypodd_ct_catalog["magnitude"], 
            '.', 
            markersize=5.0, 
            alpha=1.0, 
            rasterized=True, 
            label=f"HypoDD: {len(hypodd_ct_catalog['magnitude'].dropna())}"
        )
    
    if not standard_catalog.empty:
        ax.plot(
            standard_catalog["time"], 
            standard_catalog["magnitude"], 
            '.', 
            markersize=5.0, 
            alpha=1.0, 
            rasterized=True, 
            label=f"Standard: {len(standard_catalog['magnitude'].dropna())}"
        )

    ax.set_xlim(config["starttime"], config["endtime"])
    ax.set_ylabel("Magnitude")
    ax.set_ylim(bottom=-1)
    ax.legend(markerscale=2)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    ax.set_title(f"Magnitude vs Time - {config['region']}")
    fig.savefig("earthquake_magnitude_time.png", bbox_inches="tight", dpi=300)
    plt.close()

    print("Visualization plots created successfully")

    # MinIOにアップロード
    try:
        from minio import Minio
        minioClient = Minio(s3_url, access_key="minio", secret_key="minio123", secure=secure)
        if not minioClient.bucket_exists(bucket_name):
            minioClient.make_bucket(bucket_name)

        # HTMLファイル
        for html_file in ["hypodd_ct_catalog.html", "gamma_catalog.html", "standard_catalog.html"]:
            if os.path.exists(html_file):
                minioClient.fput_object(bucket_name, f"{config['region']}/{html_file}", html_file)

        # PNGファイル
        for png_file in ["earthquake_frequency_time.png", "earthquake_magnitude_frequency.png", "earthquake_magnitude_time.png"]:
            if os.path.exists(png_file):
                minioClient.fput_object(bucket_name, f"{config['region']}/{png_file}", png_file)

        print(f"Visualization files uploaded to MinIO: {bucket_name}")
    except Exception as err:
        print(f"WARNING: Could not upload to MinIO: {err}")

    print("Visualization completed successfully")

if __name__ == "__main__":
    main() 