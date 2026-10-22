"""Prune expiring storefront telemetry and old idempotency records."""

from __future__ import annotations

import logging
import os

import psycopg

from app import DB_APP_SECRET_ARN, connection_string, read_secret

logger = logging.getLogger("northstar.retention")


def main() -> None:
    event_days = int(os.environ.get("EVENT_RETENTION_DAYS", "90"))
    analytics_days = int(os.environ.get("ANALYTICS_RETENTION_DAYS", "30"))
    order_days = int(os.environ.get("ORDER_RETENTION_DAYS", "400"))
    if min(event_days, analytics_days, order_days) < 1:
        raise ValueError("Retention windows must be positive day counts.")
    credentials = read_secret(DB_APP_SECRET_ARN)
    with psycopg.connect(connection_string(credentials)) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM customer_events
                WHERE created_at < now() - make_interval(days => %s)
                """,
                (event_days,),
            )
            event_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM recommendation_offers o
                WHERE o.expires_at < now()
                  AND NOT EXISTS (
                      SELECT 1 FROM customer_events e WHERE e.offer_id = o.offer_id
                  )
                """
            )
            offer_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM experiment_assignments
                WHERE assigned_at < now() - make_interval(days => %s)
                """,
                (event_days,),
            )
            assignment_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM recommendation_requests
                WHERE created_at < now() - make_interval(days => %s)
                """,
                (analytics_days,),
            )
            request_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM recommendation_rate_limits
                WHERE window_start < now() - interval '1 day'
                """
            )
            limit_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM order_webhook_items i
                USING order_webhook_events e
                WHERE i.event_id = e.event_id
                  AND e.received_at < now() - make_interval(days => %s)
                """,
                (order_days,),
            )
            order_item_rows = cursor.rowcount
            cursor.execute(
                """
                DELETE FROM order_webhook_events
                WHERE received_at < now() - make_interval(days => %s)
                """,
                (order_days,),
            )
            order_rows = cursor.rowcount
    logger.info(
        "Retention cleanup completed events=%s offers=%s assignments=%s "
        "recommendation_requests=%s rate_limits=%s order_items=%s orders=%s",
        event_rows,
        offer_rows,
        assignment_rows,
        request_rows,
        limit_rows,
        order_item_rows,
        order_rows,
    )


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    main()
