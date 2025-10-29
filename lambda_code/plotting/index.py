#!/usr/bin/env python3
"""
Plotting Lambda Function
Generates matplotlib plots from DynamoDB data, exposed via API Gateway.
"""

import io
import json
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple

import boto3
from boto3.dynamodb.conditions import Key

# Configure matplotlib for headless environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402


@dataclass
class Config:
    bucket_name: str
    table_name: str = 'S3-object-size-history'
    window_seconds: int = 10
    plot_key: str = 'plot'


s3_client = boto3.client('s3')
ddb = boto3.resource('dynamodb')


def _to_int(n: Any) -> int:
    if isinstance(n, Decimal):
        return int(n)
    return int(n)


def _get_config(event: Dict[str, Any]) -> Config:
    """Get configuration from environment variables and query parameters."""
    qs = (event or {}).get('queryStringParameters') or {}
    
    # Get bucket name from query param or environment variable
    bucket = qs.get('bucket') or os.environ.get('BUCKET_NAME')
    if not bucket:
        raise ValueError("Bucket name not provided. Set env BUCKET_NAME or pass ?bucket=")
    
    # Get window seconds from query param or environment variable
    window_str = qs.get('window') or os.environ.get('WINDOW_SECONDS', '10')
    try:
        window = int(window_str)
    except Exception:
        window = 10
    
    # Get table name from environment variable
    table = os.environ.get('TABLE_NAME', 'S3-object-size-history')
    
    return Config(bucket_name=bucket, table_name=table, window_seconds=window)


def _query_last_window(table, bucket: str, now_epoch: int, window_seconds: int) -> List[Dict[str, Any]]:
    """Query DynamoDB for items in the last window."""
    since = now_epoch - window_seconds
    items: List[Dict[str, Any]] = []
    kwargs = {
        'KeyConditionExpression': Key('bucket_name').eq(bucket) & Key('timestamp').gte(since),
        'ScanIndexForward': True,
    }
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get('Items', []))
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    return items


def _query_all_for_max(table, bucket: str) -> int:
    """Query entire partition for bucket to compute historical max of total_size."""
    max_size = 0
    kwargs = {
        'KeyConditionExpression': Key('bucket_name').eq(bucket) & Key('timestamp').gte(0),
        'ScanIndexForward': True,
    }
    while True:
        resp = table.query(**kwargs)
        for it in resp.get('Items', []):
            sz = _to_int(it.get('total_size', 0))
            if sz > max_size:
                max_size = sz
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    return max_size


def _generate_plot(points: List[Tuple[int, int]], historical_high: int) -> bytes:
    """Generate PNG bytes with matplotlib.
    points: list of (timestamp, size)
    """
    # Prepare data
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)

    if xs:
        # Normalize X to human-readable seconds offset from first point
        x0 = xs[0]
        x_secs = [x - x0 for x in xs]
        ax.plot(x_secs, ys, marker='o', linewidth=1.5, color='#1f77b4', label='Last window size')
    else:
        # No data, draw empty axes
        ax.plot([], [], label='No points in window')

    # Historical high line
    ax.axhline(y=historical_high, color='#d62728', linestyle='--', linewidth=1.2, label='Historical high')

    ax.set_xlabel('Seconds (relative)')
    ax.set_ylabel('Total size (bytes)')
    ax.set_title('Bucket size (last window) with historical high')
    ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.6)
    ax.legend(loc='best', fontsize=8)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for API Gateway requests."""
    try:
        cfg = _get_config(event)
        table = ddb.Table(cfg.table_name)

        now_epoch = int(time.time())

        # Query window points and whole-history max (both via Query)
        window_items = _query_last_window(table, cfg.bucket_name, now_epoch, cfg.window_seconds)
        # Convert to simple tuples and sort by timestamp
        points: List[Tuple[int, int]] = []
        for it in sorted(window_items, key=lambda x: _to_int(x['timestamp'])):
            ts = _to_int(it['timestamp'])
            size = _to_int(it.get('total_size', 0))
            points.append((ts, size))

        historical_high = _query_all_for_max(table, cfg.bucket_name)

        # Generate plot PNG
        png_bytes = _generate_plot(points, historical_high)

        # Write to S3 as 'plot'
        s3_client.put_object(
            Bucket=cfg.bucket_name,
            Key=cfg.plot_key,
            Body=png_bytes,
            ContentType='image/png',
            CacheControl='no-cache'
        )

        body = {
            'bucket': cfg.bucket_name,
            's3_key': cfg.plot_key,
            'window_seconds': cfg.window_seconds,
            'num_points': len(points),
            'historical_high': historical_high,
        }
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(body)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

