import json
import logging
import os
from decimal import Decimal
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Attr

from domain import ValidationError, summarize, validate_expense

logger = logging.getLogger()
logger.setLevel(logging.INFO)
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


class DecimalEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return super().default(value)


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body or {}, cls=DecimalEncoder),
    }


def lambda_handler(event, _context):
    method = event["requestContext"]["http"]["method"]
    path = event.get("rawPath", "/")
    logger.info(json.dumps({"method": method, "path": path}))
    try:
        if method == "POST" and path == "/expenses":
            item = validate_expense(json.loads(event.get("body") or "{}"))
            item["id"] = str(uuid4())
            table.put_item(Item=item)
            return response(201, item)

        if method == "GET" and path == "/expenses":
            params = event.get("queryStringParameters") or {}
            filters = []
            if params.get("month"):
                filters.append(Attr("month").eq(params["month"]))
            if params.get("category"):
                filters.append(Attr("category").eq(params["category"].lower()))
            kwargs = {}
            if filters:
                expression = filters[0]
                for current in filters[1:]:
                    expression &= current
                kwargs["FilterExpression"] = expression
            items = table.scan(**kwargs).get("Items", [])
            return response(200, sorted(items, key=lambda item: item["date"], reverse=True))

        if method == "GET" and path.startswith("/summary/"):
            month = event.get("pathParameters", {}).get("month", "")
            items = table.scan(FilterExpression=Attr("month").eq(month)).get("Items", [])
            return response(200, {"month": month, **summarize(items)})

        if method == "DELETE" and path.startswith("/expenses/"):
            expense_id = event.get("pathParameters", {}).get("id")
            table.delete_item(Key={"id": expense_id})
            return response(204)

        return response(404, {"error": "Route not found"})
    except (ValidationError, json.JSONDecodeError) as exc:
        return response(400, {"error": str(exc)})
    except Exception:
        logger.exception("Unhandled request error")
        return response(500, {"error": "Internal server error"})

