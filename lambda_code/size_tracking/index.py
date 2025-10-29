#!/usr/bin/env python3
"""
Size-tracking Lambda Function
Triggered by S3 events, calculates and records bucket size to DynamoDB.
"""

import json
import boto3
import time
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get table name from environment variable (set by CDK)
TABLE_NAME = os.environ.get('TABLE_NAME', 'S3-object-size-history')
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for S3 event triggers.
    
    Args:
        event: S3 event containing bucket and object information
        context: Lambda context object
    
    Returns:
        Response with status code and message
    """
    
    try:
        # Extract bucket name from the S3 event
        # S3 events can contain multiple records
        for record in event.get('Records', []):
            # Get bucket name from the event
            bucket_name = record['s3']['bucket']['name']
            event_name = record['eventName']
            
            print(f"Processing S3 event: {event_name} for bucket: {bucket_name}")
            
            # Calculate total size and count of all objects in the bucket
            total_size, object_count = calculate_bucket_metrics(bucket_name)
            
            # Get current timestamp
            timestamp = int(time.time())  # Unix timestamp (epoch)
            recorded_at = datetime.utcnow().isoformat() + 'Z'  # ISO format for display
            
            # Prepare item for DynamoDB
            item = {
                'bucket_name': bucket_name,
                'timestamp': timestamp,
                'total_size': total_size,
                'object_count': object_count,
                'recorded_at': recorded_at,
                'triggered_by': event_name  # Track what type of event triggered this
            }
            
            # Write to DynamoDB
            write_to_dynamodb(item)
            
            print(f"Successfully recorded metrics - Size: {total_size} bytes, Objects: {object_count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Bucket size tracking completed successfully',
                'bucket': bucket_name,
                'total_size': total_size,
                'object_count': object_count,
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        print(f"Error in size-tracking lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def calculate_bucket_metrics(bucket_name: str) -> tuple:
    """
    Calculate total size and count of all objects in the bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
    
    Returns:
        Tuple of (total_size, object_count)
    """
    total_size = 0
    object_count = 0
    
    try:
        # Use paginator to handle buckets with many objects
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        for page in page_iterator:
            # Check if the bucket has any contents
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_size += obj['Size']
                    object_count += 1
        
        print(f"Calculated metrics for {bucket_name}: {object_count} objects, {total_size} bytes")
        
    except Exception as e:
        print(f"Error calculating bucket metrics: {str(e)}")
        # If there's an error (e.g., bucket doesn't exist), return 0s
        # This handles the case when all objects are deleted
        
    return total_size, object_count


def write_to_dynamodb(item: Dict[str, Any]) -> None:
    """
    Write metrics to DynamoDB table.
    
    Args:
        item: Dictionary containing metrics to write
    """
    try:
        response = table.put_item(Item=item)
        print(f"Successfully wrote to DynamoDB: {item}")
        
    except Exception as e:
        print(f"Error writing to DynamoDB: {str(e)}")
        raise

