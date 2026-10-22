import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_MASTER_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:000000000000:secret:master")
os.environ.setdefault("DB_APP_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:000000000000:secret:app")
os.environ.setdefault("METRICS_LAMBDA_ARN", "arn:aws:lambda:us-east-1:000000000000:function:metrics")
os.environ.setdefault("COGNITO_USER_POOL_ID", "us-east-1_example")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "example-client")
os.environ.setdefault("METRIC_NAMESPACE", "northstar/Commerce")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as application
import lambda_metrics
import load_test
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.products = [
            {
                "product_id": "camera-x2",
                "name": "Summit Camera",
                "category": "Camera gear",
                "price": 849.0,
                "rating": 4.9,
            },
            {
                "product_id": "trail-pack-28",
                "name": "Trail Pack",
                "category": "Outdoor",
                "price": 94.0,
                "rating": 4.8,
            },
        ]
        self.history = [{
            "event_type": "product_view",
            "product_id": "camera-x2",
            "query": None,
            "created_at": datetime(2026, 10, 22, tzinfo=UTC),
        }]

    @patch.object(application.bedrock_client, "converse")
    def test_recommendations_are_limited_to_valid_catalog_items(self, converse):
        converse.return_value = {
            "output": {
                "message": {
                    "content": [{
                        "text": json.dumps({
                            "recommendations": [
                                {"product_id": "trail-pack-28", "reason": "Useful on a hike.", "score": 0.91},
                                {"product_id": "not-in-catalog", "reason": "Invented.", "score": 0.99},
                                {"product_id": "camera-x2", "reason": "Pairs with the viewed camera.", "score": 0.87},
                            ]
                        })
                    }]
                }
            }
        }

        result = application.generate_recommendations(self.history, self.products)

        self.assertEqual([item["product_id"] for item in result], ["trail-pack-28", "camera-x2"])
        self.assertEqual(result[0]["score"], 0.91)
        prompt = converse.call_args.kwargs["messages"][0]["content"][0]["text"]
        self.assertIn("camera-x2", prompt)
        self.assertIn("trail-pack-28", prompt)

    def test_seed_catalog_has_unique_ids_for_all_demo_recommendations(self):
        product_ids = [product["product_id"] for product in application.PRODUCTS]

        self.assertEqual(len(product_ids), 18)
        self.assertEqual(len(product_ids), len(set(product_ids)))
        self.assertIn("ridge-poles", product_ids)
        self.assertIn("merino-socks", product_ids)
        self.assertIn("packing-cubes", product_ids)
        self.assertIn("alpine-hammock", product_ids)
        self.assertIn("atlas-binoculars", product_ids)
        self.assertIn("camera-case", product_ids)
        self.assertIn("polarizer-filter", product_ids)
        self.assertIn("trail-headlamp", product_ids)
        self.assertIn("thermos-flask", product_ids)
        self.assertIn("camera-battery", product_ids)

    @patch.object(application.bedrock_client, "converse")
    def test_recommendations_accept_eight_products(self, converse):
        product_ids = [product["product_id"] for product in application.PRODUCTS[:8]]
        converse.return_value = {
            "output": {
                "message": {
                    "content": [{
                        "text": json.dumps({
                            "recommendations": [
                                {"product_id": product_id, "reason": "Matches the outdoor collection.", "score": 0.8}
                                for product_id in product_ids
                            ]
                        })
                    }]
                }
            }
        }

        result = application.generate_recommendations(self.history, list(application.PRODUCTS))

        self.assertEqual(len(result), 8)
        self.assertEqual([item["product_id"] for item in result], product_ids)
        prompt = converse.call_args.kwargs["system"][0]["text"]
        self.assertIn("up to eight unique catalog products", prompt)

    @patch.object(application.bedrock_client, "converse")
    def test_invalid_model_json_fails_explicitly(self, converse):
        converse.return_value = {
            "output": {"message": {"content": [{"text": "not-json"}]}}
        }

        with self.assertRaises(HTTPException) as error:
            application.generate_recommendations(self.history, self.products)

        self.assertEqual(error.exception.status_code, 502)

    @patch.object(application.bedrock_client, "converse")
    def test_invented_or_invalid_model_scores_are_rejected(self, converse):
        converse.return_value = {
            "output": {
                "message": {
                    "content": [{
                        "text": json.dumps({
                            "recommendations": [
                                {"product_id": "camera-x2", "reason": "Bad confidence.", "score": 4}
                            ]
                        })
                    }]
                }
            }
        }

        with self.assertRaises(HTTPException) as error:
            application.generate_recommendations(self.history, self.products)

        self.assertEqual(error.exception.status_code, 502)

    def test_browser_event_payload_rejects_unverified_purchase(self):
        with self.assertRaises(ValidationError):
            application.CustomerEvent(event_type="purchase", product_id="camera-x2")

    def test_recommendation_events_require_an_offer_id(self):
        with self.assertRaises(ValidationError):
            application.CustomerEvent(
                event_type="recommendation_impression", product_id="camera-x2"
            )
        with self.assertRaises(ValidationError):
            application.CustomerEvent(
                event_type="product_view",
                product_id="camera-x2",
                offer_id="a" * 43,
            )

    def test_recommendation_impression_requires_matching_unexpired_offer(self):
        connection_pool = MagicMock()
        connection = connection_pool.connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [{"exists": 1}, None]

        with self.assertRaises(HTTPException) as error:
            application.record_customer_event(
                "store:session-a",
                application.CustomerEvent(
                    event_type="recommendation_impression",
                    product_id="camera-x2",
                    offer_id="b" * 43,
                ),
                connection_pool,
            )

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(cursor.execute.call_count, 2)
        connection.commit.assert_not_called()

    def test_recommendation_click_requires_a_recorded_impression(self):
        connection_pool = MagicMock()
        connection = connection_pool.connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [{"exists": 1}, {"exists": 1}, None]

        with self.assertRaises(HTTPException) as error:
            application.record_customer_event(
                "store:session-a",
                application.CustomerEvent(
                    event_type="recommendation_click",
                    product_id="camera-x2",
                    offer_id="c" * 43,
                ),
                connection_pool,
            )

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(cursor.execute.call_count, 3)
        connection.commit.assert_not_called()

    def test_non_admin_cannot_read_store_wide_analytics(self):
        with self.assertRaises(HTTPException) as error:
            application.summary({"sub": "customer", "cognito:groups": []}, None)

        self.assertEqual(error.exception.status_code, 403)

    def test_store_session_cookie_is_opaque_http_only_and_secure_in_production(self):
        response = Response()
        request = make_request(b"")
        with patch.dict(os.environ, {"STORE_SESSION_COOKIE_SECURE": "true"}):
            result = application.create_store_session(request, response)

        cookie = response.headers["set-cookie"].lower()
        self.assertEqual(result, {"created": True})
        self.assertIn("httponly", cookie)
        self.assertIn("secure", cookie)
        self.assertIn("samesite=lax", cookie)
        self.assertNotIn("session", json.dumps(result))

    def test_store_session_endpoint_preserves_existing_valid_session(self):
        session_id = "a" * 43
        request = make_request(b"")
        request.scope["headers"] = [
            (b"cookie", f"northstar_store_session={session_id}".encode())
        ]
        response = Response()

        result = application.create_store_session(request, response)

        self.assertEqual(result, {"created": False})
        self.assertNotIn("set-cookie", response.headers)

    def test_store_session_identity_is_taken_from_validated_cookie(self):
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"cookie", b"northstar_store_session=" + b"a" * 43)],
            "query_string": b"",
            "server": ("test", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
        })

        self.assertEqual(application.require_store_session(request), "store:" + "a" * 43)

    def test_empty_store_history_uses_catalog_without_invoking_bedrock(self):
        database = MagicMock()
        request = MagicMock()
        request.headers.get.return_value = None
        with (
            patch.object(application, "read_customer_context", return_value=(0, [], self.products)),
            patch.object(application.bedrock_client, "converse") as converse,
        ):
            result = application.get_recommendations("store:anonymous", request, database)

        self.assertEqual(len(result["items"]), 2)
        self.assertFalse(result["cache_hit"])
        converse.assert_not_called()

    def test_control_arm_uses_top_rated_products_even_with_customer_history(self):
        database = MagicMock()
        request = MagicMock()
        request.headers.get.return_value = None
        with (
            patch.object(
                application,
                "read_customer_context",
                return_value=(2, self.history, self.products),
            ),
            patch.object(application.bedrock_client, "converse") as converse,
        ):
            result = application.get_recommendations(
                "store:control-session", request, database, experiment_arm="control"
            )

        self.assertEqual(
            [item["product_id"] for item in result["items"]],
            ["camera-x2", "trail-pack-28"],
        )
        self.assertEqual(result["experiment_arm"], "control")
        converse.assert_not_called()

    def test_treatment_arm_uses_personalized_recommendations_with_history(self):
        database = MagicMock()
        request = MagicMock()
        request.headers.get.return_value = None
        with (
            patch.object(
                application,
                "read_customer_context",
                return_value=(2, self.history, self.products),
            ),
            patch.object(
                application,
                "generate_recommendations",
                return_value=[{"product_id": "trail-pack-28"}],
            ) as generate,
        ):
            result = application.get_recommendations(
                "store:treatment-session", request, database, experiment_arm="treatment"
            )

        self.assertEqual(
            [item["product_id"] for item in result["items"]],
            ["trail-pack-28", "camera-x2"],
        )
        self.assertEqual(result["experiment_arm"], "treatment")
        generate.assert_called_once_with(self.history, self.products)

    def test_experiment_assignment_uses_existing_database_assignment(self):
        connection_pool = MagicMock()
        connection = connection_pool.connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {"arm": "treatment"}

        with patch.object(application.secrets, "randbelow", return_value=0):
            arm = application.get_or_create_experiment_arm("store:stable", connection_pool)

        self.assertEqual(arm, "treatment")
        self.assertEqual(
            cursor.execute.call_args_list[0].args[1],
            ("store:stable", "control"),
        )
        self.assertTrue(
            any(
                "ON CONFLICT (customer_id) DO NOTHING" in call.args[0]
                for call in cursor.execute.call_args_list
            )
        )
        connection.commit.assert_called_once()

    def test_experiment_summary_uses_exposed_sessions_and_verified_orders(self):
        result = application.build_experiment_summary(
            [
                {
                    "arm": "control",
                    "assigned_sessions": 10,
                    "exposed_sessions": 8,
                    "impressions": 20,
                    "clicks": 2,
                    "purchasing_sessions": 1,
                    "gross_sales_usd": 849.0,
                },
                {
                    "arm": "treatment",
                    "assigned_sessions": 12,
                    "exposed_sessions": 10,
                    "impressions": 30,
                    "clicks": 6,
                    "purchasing_sessions": 3,
                    "gross_sales_usd": 1800.0,
                },
            ],
            7,
        )

        self.assertEqual(result["arms"]["control"]["ctr_percent"], 10)
        self.assertEqual(result["arms"]["control"]["conversion_percent"], 12.5)
        self.assertEqual(result["arms"]["treatment"]["ctr_percent"], 20)
        self.assertEqual(result["arms"]["treatment"]["conversion_percent"], 30)
        self.assertEqual(result["arms"]["control"]["gross_sales_usd"], 849)
        self.assertIsNotNone(result["arms"]["control"]["ctr_95ci_percent"])
        self.assertIsNotNone(result["arms"]["control"]["conversion_95ci_percent"])
        self.assertEqual(result["treatment_ctr_relative_change_percent"], 100)
        self.assertEqual(result["treatment_conversion_relative_change_percent"], 140)

    def test_experiment_summary_handles_missing_control_baseline(self):
        result = application.build_experiment_summary([], 7)

        self.assertIsNone(result["treatment_ctr_relative_change_percent"])
        self.assertIsNone(result["treatment_conversion_relative_change_percent"])
        self.assertEqual(result["arms"]["control"]["assigned_sessions"], 0)

    def test_load_test_requires_explicit_matching_https_target_and_limits(self):
        target = "https://store.example.com"
        self.assertEqual(
            load_test.validate_target(target, "store.example.com", 4, 60, 1),
            target,
        )
        for invalid in (
            (target, "other.example.com", 4, 60, 1),
            ("http://store.example.com", "store.example.com", 4, 60, 1),
            (target, "store.example.com", 11, 60, 1),
            (target, "store.example.com", 4, 181, 1),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                load_test.validate_target(*invalid)

    def test_load_test_summary_reports_latency_and_http_errors(self):
        result = load_test.summarize_results(
            [
                {"status": 200, "latency_ms": 20},
                {"status": 503, "latency_ms": 80},
                {"status": None, "latency_ms": 100},
            ],
            2,
            2,
        )

        self.assertEqual(result["requests"], 3)
        self.assertEqual(result["failed_requests"], 2)
        self.assertEqual(result["error_rate_percent"], 66.67)
        self.assertEqual(result["latency_ms"]["p95"], 100)
        self.assertEqual(result["status_codes"], {"200": 1, "503": 1, "network_error": 1})

    def test_order_webhook_rejects_invalid_signature_before_database_access(self):
        body = b'{"order_id":"order-1"}'
        request = make_request(body)
        pool = MagicMock()
        timestamp = str(int(time.time()))
        signature = "sha256=" + "0" * 64
        with patch.object(application, "order_webhook_secret", "test-secret"):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    application.ingest_order_webhook(
                        request, "evt-1", timestamp, signature, pool
                    )
                )

        self.assertEqual(error.exception.status_code, 401)
        pool.connection.assert_not_called()

    def test_order_webhook_rejects_future_order_time(self):
        with self.assertRaises(ValidationError):
            application.TrustedOrder(
                order_id="order-future",
                occurred_at=datetime.now(UTC) + timedelta(minutes=6),
                total_amount=Decimal("10.00"),
                items=[{"product_id": "camera-x2", "quantity": 1}],
            )

    def test_order_webhook_verifies_signature_and_records_purchase(self):
        payload = {
            "order_id": "order-42",
            "session_id": "a" * 43,
            "occurred_at": datetime.now(UTC).isoformat(),
            "total_amount": "1698.00",
            "currency": "USD",
            "items": [{"product_id": "camera-x2", "quantity": 2}],
        }
        body = json.dumps(payload).encode()
        timestamp = str(int(time.time()))
        signature = "sha256=" + hmac.new(
            b"test-secret",
            timestamp.encode() + b"." + body,
            hashlib.sha256,
        ).hexdigest()
        cursor = FakeOrderCursor()
        pool = FakeOrderPool(cursor)
        with (
            patch.object(application, "order_webhook_secret", "test-secret"),
            patch.object(application.lambda_client, "invoke", return_value={"StatusCode": 202}),
        ):
            result = asyncio.run(
                application.ingest_order_webhook(
                    make_request(body), "evt-42", timestamp, signature, pool
                )
            )

        self.assertEqual(
            result,
            {"accepted": True, "duplicate": False, "metrics_queued": True},
        )
        self.assertTrue(any("INSERT INTO order_webhook_items" in stmt for stmt in cursor.statements))
        self.assertIn("VALUES (%s, 'purchase', %s, %s)", cursor.statements[-1])
        self.assertIn(
            (f"store:{payload['session_id']}", "camera-x2", datetime.fromisoformat(payload["occurred_at"])),
            cursor.parameters,
        )
        order_insert = next(
            parameters
            for statement, parameters in zip(cursor.statements, cursor.parameters)
            if "INSERT INTO order_webhook_events" in statement
        )
        self.assertEqual(order_insert[-2:], (Decimal("1698.00"), "USD"))

    def test_order_webhook_redelivery_is_idempotent(self):
        payload = {
            "order_id": "order-42",
            "session_id": "a" * 43,
            "occurred_at": datetime.now(UTC).isoformat(),
            "total_amount": "1698.00",
            "currency": "USD",
            "items": [{"product_id": "camera-x2", "quantity": 2}],
        }
        body = json.dumps(payload).encode()
        canonical_order = application.TrustedOrder.model_validate(payload).model_dump(mode="json")
        canonical = json.dumps(canonical_order, sort_keys=True, separators=(",", ":"))
        cursor = FakeOrderCursor(
            prior={"event_id": "evt-42", "payload_sha256": hashlib.sha256(canonical.encode()).hexdigest()}
        )
        timestamp = str(int(time.time()))
        signature = "sha256=" + hmac.new(
            b"test-secret",
            timestamp.encode() + b"." + body,
            hashlib.sha256,
        ).hexdigest()
        with patch.object(application, "order_webhook_secret", "test-secret"):
            result = asyncio.run(
                application.ingest_order_webhook(
                    make_request(body), "evt-42", timestamp, signature, FakeOrderPool(cursor)
                )
            )

        self.assertEqual(result, {"accepted": True, "duplicate": True})
        self.assertFalse(any("INSERT INTO customer_events" in stmt for stmt in cursor.statements))


class MetricsLambdaTests(unittest.TestCase):
    def test_product_view_emits_event_and_product_metrics(self):
        event_time = datetime(2026, 10, 22, 5, 0, tzinfo=UTC)
        event = {
            "event_id": 42,
            "event_type": "product_view",
            "product_id": "camera-x2",
            "occurred_at": event_time.isoformat(),
        }
        with patch.object(lambda_metrics.cloudwatch, "put_metric_data") as put_metric_data:
            result = lambda_metrics.handler(event, None)

        self.assertEqual(json.loads(result["body"]), {"recorded": 42})
        metric_data = put_metric_data.call_args.kwargs["MetricData"]
        self.assertEqual(len(metric_data), 2)
        self.assertEqual(metric_data[1]["MetricName"], "ProductViews")
        self.assertEqual(metric_data[1]["Timestamp"], event_time)

    def test_invalid_customer_event_fails(self):
        with self.assertRaises(ValueError):
            lambda_metrics.handler({"event_id": 1, "event_type": "unknown"}, None)


def make_request(body):
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/webhooks/orders",
            "headers": [],
            "query_string": b"",
            "server": ("test", 443),
            "client": ("127.0.0.1", 1234),
            "scheme": "https",
        },
        receive,
    )


class FakeOrderCursor:
    def __init__(self, prior=None):
        self.statement = ""
        self.statements = []
        self.parameters = []
        self.prior = prior

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement, parameters=None):
        self.statement = statement
        self.statements.append(statement)
        if parameters is not None:
            self.parameters.append(parameters)

    def fetchall(self):
        if "SELECT product_id FROM products" in self.statement:
            return [{"product_id": "camera-x2"}]
        return []

    def fetchone(self):
        if "RETURNING event_id" in self.statement:
            return None if self.prior else {"event_id": "evt-42"}
        if "SELECT event_id, payload_sha256 FROM order_webhook_events" in self.statement:
            return self.prior
        if "RETURNING id" in self.statement:
            return {"id": 42}
        return None


class FakeOrderConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def cursor(self):
        return self._cursor

    def commit(self):
        return None

    def rollback(self):
        return None


class FakeOrderPool:
    def __init__(self, cursor):
        self._connection = FakeOrderConnection(cursor)

    def connection(self):
        return self._connection


if __name__ == "__main__":
    unittest.main()
