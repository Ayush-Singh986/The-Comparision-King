import json
import os
from datetime import datetime

import boto3

cloudwatch = boto3.client("cloudwatch", region_name=os.environ["AWS_REGION"])
NAMESPACE = os.environ["METRIC_NAMESPACE"]
ALLOWED_EVENT_TYPES = {
    "product_view",
    "search",
    "purchase",
    "recommendation_impression",
    "recommendation_click",
}


def handler(event, _context):
    event_type = event.get("event_type")
    event_id = event.get("event_id")
    product_id = event.get("product_id")
    if (
        event_type not in ALLOWED_EVENT_TYPES
        or not isinstance(event_id, int)
        or (product_id is not None and not isinstance(product_id, str))
    ):
        raise ValueError("The customer event is missing a valid event_type or event_id.")
    occurred_at = datetime.fromisoformat(event["occurred_at"])
    metric_data = [
        {
            "MetricName": "CustomerEvents",
            "Dimensions": [{"Name": "EventType", "Value": event_type}],
            "Timestamp": occurred_at,
            "Value": 1,
            "Unit": "Count",
        }
    ]
    if event_type == "product_view" and product_id:
        metric_data.append(
            {
                "MetricName": "ProductViews",
                "Dimensions": [{"Name": "ProductId", "Value": product_id}],
                "Timestamp": occurred_at,
                "Value": 1,
                "Unit": "Count",
            }
        )
    cloudwatch.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=metric_data,
    )
    return {"statusCode": 200, "body": json.dumps({"recorded": event_id})}
