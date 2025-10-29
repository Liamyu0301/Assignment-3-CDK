#!/usr/bin/env python3
"""
Driver Lambda Function
Orchestrates S3 operations and calls plotting API for testing.
"""

import json
import time
import urllib.request
import urllib.error
import os
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Driver Lambda handler that performs S3 operations and calls plotting API.
    
    Args:
        event: Lambda event (can be empty for manual invocation)
        context: Lambda context object
    
    Returns:
        Response with operation results and plot generation status
    """
    
    try:
        # Get configuration from environment variables (set by CDK)
        BUCKET_NAME = os.environ.get('BUCKET_NAME')
        PLOTTING_API_URL = os.environ.get('PLOTTING_API_URL')
        
        if not BUCKET_NAME:
            raise ValueError("BUCKET_NAME environment variable not set")
        if not PLOTTING_API_URL or PLOTTING_API_URL == "PLACEHOLDER":
            raise ValueError("PLOTTING_API_URL environment variable not set or is placeholder")
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        results = {
            "operations": [],
            "plot_generation": None,
            "errors": []
        }
        
        print(f"Starting driver lambda operations on bucket: {BUCKET_NAME}")
        
        # Operation 1: Create assignment1.txt
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key="assignment1.txt",
                Body="Empty Assignment 1",
                ContentType="text/plain"
            )
            results["operations"].append({
                "step": 1,
                "operation": "CREATE assignment1.txt",
                "content": "Empty Assignment 1",
                "size": 18,
                "status": "success"
            })
            print("✓ Created assignment1.txt (18 bytes)")
            
        except Exception as e:
            error_msg = f"Failed to create assignment1.txt: {str(e)}"
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        
        # Sleep between operations (longer for first operation to ensure tracking lambda completes)
        print("Sleeping 6 seconds...")
        time.sleep(6)
        
        # Operation 2: Update assignment1.txt
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key="assignment1.txt",
                Body="Empty Assignment 2222222222",
                ContentType="text/plain"
            )
            results["operations"].append({
                "step": 2,
                "operation": "UPDATE assignment1.txt",
                "content": "Empty Assignment 2222222222",
                "size": 27,
                "status": "success"
            })
            print("✓ Updated assignment1.txt (27 bytes)")
            
        except Exception as e:
            error_msg = f"Failed to update assignment1.txt: {str(e)}"
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        
        # Sleep between operations
        print("Sleeping 2 seconds...")
        time.sleep(2)
        
        # Operation 3: Delete assignment1.txt
        try:
            s3_client.delete_object(
                Bucket=BUCKET_NAME,
                Key="assignment1.txt"
            )
            results["operations"].append({
                "step": 3,
                "operation": "DELETE assignment1.txt",
                "content": "",
                "size": 0,
                "status": "success"
            })
            print("✓ Deleted assignment1.txt (0 bytes)")
            
        except Exception as e:
            error_msg = f"Failed to delete assignment1.txt: {str(e)}"
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        
        # Sleep between operations
        print("Sleeping 2 seconds...")
        time.sleep(2)
        
        # Operation 4: Create assignment2.txt
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key="assignment2.txt",
                Body="33",
                ContentType="text/plain"
            )
            results["operations"].append({
                "step": 4,
                "operation": "CREATE assignment2.txt",
                "content": "33",
                "size": 2,
                "status": "success"
            })
            print("✓ Created assignment2.txt (2 bytes)")
            
        except Exception as e:
            error_msg = f"Failed to create assignment2.txt: {str(e)}"
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        
        # Wait for size-tracking lambda to process all events
        print("Waiting 2 seconds for size-tracking lambda to process all events...")
        time.sleep(2)
        
        # Operation 5: Call plotting API
        try:
            print(f"Calling plotting API: {PLOTTING_API_URL}")
            
            # Use urllib instead of requests
            req = urllib.request.Request(PLOTTING_API_URL)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    plot_data = json.loads(response.read().decode('utf-8'))
                    results["plot_generation"] = {
                        "status": "success",
                        "api_response": plot_data,
                        "plot_url": f"s3://{BUCKET_NAME}/plot"
                    }
                    print(f"✓ Plot generated successfully: {plot_data}")
                else:
                    error_msg = f"Plotting API returned status {response.status}"
                    results["plot_generation"] = {
                        "status": "failed",
                        "error": error_msg
                    }
                    results["errors"].append(error_msg)
                    print(f"✗ {error_msg}")
                
        except urllib.error.URLError as e:
            error_msg = f"Failed to call plotting API (URL error): {str(e)}"
            results["plot_generation"] = {
                "status": "failed", 
                "error": error_msg
            }
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        except Exception as e:
            error_msg = f"Failed to call plotting API: {str(e)}"
            results["plot_generation"] = {
                "status": "failed", 
                "error": error_msg
            }
            results["errors"].append(error_msg)
            print(f"✗ {error_msg}")
        
        # Summary
        successful_ops = len([op for op in results["operations"] if op["status"] == "success"])
        total_ops = len(results["operations"])
        
        print(f"\n=== DRIVER LAMBDA SUMMARY ===")
        print(f"Successful operations: {successful_ops}/{total_ops}")
        print(f"Plot generation: {results['plot_generation']['status'] if results['plot_generation'] else 'Not attempted'}")
        print(f"Errors: {len(results['errors'])}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Driver lambda completed',
                'successful_operations': successful_ops,
                'total_operations': total_ops,
                'plot_generated': results["plot_generation"]["status"] == "success" if results["plot_generation"] else False,
                'results': results
            }, indent=2)
        }
        
    except Exception as e:
        error_msg = f"Driver lambda failed: {str(e)}"
        print(f"✗ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }

