from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import threading
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any

import boto3
import jwt
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jwt import PyJWKClient
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from psycopg import Connection, sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("northstar")

AWS_REGION = os.environ["AWS_REGION"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ.get("DB_NAME", "northstar")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_MASTER_SECRET_ARN = os.environ["DB_MASTER_SECRET_ARN"]
DB_APP_SECRET_ARN = os.environ["DB_APP_SECRET_ARN"]
ORDER_WEBHOOK_SECRET_ARN = os.environ.get("ORDER_WEBHOOK_SECRET_ARN", "")
METRICS_LAMBDA_ARN = os.environ["METRICS_LAMBDA_ARN"]
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
COGNITO_USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
COGNITO_APP_CLIENT_ID = os.environ["COGNITO_APP_CLIENT_ID"]
COGNITO_ISSUER = (
    f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
)
PRODUCTS = (
    {
        "product_id": "camera-x2",
        "name": "Summit Mirrorless Camera X2",
        "category": "Camera gear",
        "price": 849.0,
        "rating": 4.9,
        "emoji": "📷",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "trail-pack-28",
        "name": "Trailblazer 28L Daypack",
        "category": "Outdoor",
        "price": 94.0,
        "rating": 4.8,
        "emoji": "🎒",
        "signals": ["views"],
    },
    {
        "product_id": "prime-lens-50",
        "name": "Peak 50mm Prime Lens",
        "category": "Camera gear",
        "price": 329.0,
        "rating": 4.9,
        "emoji": "🔭",
        "signals": ["trending"],
    },
    {
        "product_id": "camera-sling",
        "name": "Field Notes Camera Sling",
        "category": "Accessories",
        "price": 68.0,
        "rating": 4.7,
        "emoji": "👜",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "trail-shell",
        "name": "Ridgeline Waterproof Trail Shell",
        "category": "Outdoor",
        "price": 129.0,
        "rating": 4.8,
        "emoji": "🧥",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "summit-boots",
        "name": "Summit Grip Hiking Boots",
        "category": "Outdoor",
        "price": 159.0,
        "rating": 4.8,
        "emoji": "🥾",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "carbon-tripod",
        "name": "Waypoint Carbon Travel Tripod",
        "category": "Camera gear",
        "price": 119.0,
        "rating": 4.7,
        "emoji": "📸",
        "signals": ["trending"],
    },
    {
        "product_id": "field-drive",
        "name": "Fieldwork 1TB Portable SSD",
        "category": "Accessories",
        "price": 109.0,
        "rating": 4.8,
        "emoji": "💾",
        "signals": ["views"],
    },
    {
        "product_id": "ridge-poles",
        "name": "Ridgeway Carbon Trekking Poles",
        "category": "Outdoor",
        "price": 79.0,
        "rating": 4.7,
        "emoji": "🥾",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "merino-socks",
        "name": "Switchback Merino Trail Socks",
        "category": "Outdoor",
        "price": 24.0,
        "rating": 4.8,
        "emoji": "🧦",
        "signals": ["views"],
    },
    {
        "product_id": "packing-cubes",
        "name": "Wanderlight Packing Cube Set",
        "category": "Accessories",
        "price": 38.0,
        "rating": 4.6,
        "emoji": "🧳",
        "signals": ["views"],
    },
    {
        "product_id": "alpine-hammock",
        "name": "Alpine Drift Camp Hammock",
        "category": "Outdoor",
        "price": 89.0,
        "rating": 4.9,
        "emoji": "🏕️",
        "signals": ["trending"],
    },
    {
        "product_id": "atlas-binoculars",
        "name": "Atlas Compact Trail Binoculars",
        "category": "Outdoor",
        "price": 139.0,
        "rating": 4.7,
        "emoji": "🔭",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "camera-case",
        "name": "Canyon Waterproof Camera Case",
        "category": "Accessories",
        "price": 56.0,
        "rating": 4.8,
        "emoji": "📸",
        "signals": ["views"],
    },
    {
        "product_id": "polarizer-filter",
        "name": "Clearwater Polarizing Lens Filter",
        "category": "Camera gear",
        "price": 45.0,
        "rating": 4.7,
        "emoji": "🔍",
        "signals": ["trending"],
    },
    {
        "product_id": "trail-headlamp",
        "name": "Northline Rechargeable Headlamp",
        "category": "Outdoor",
        "price": 39.0,
        "rating": 4.8,
        "emoji": "🔦",
        "signals": ["views"],
    },
    {
        "product_id": "thermos-flask",
        "name": "Evergreen Trail Thermos",
        "category": "Outdoor",
        "price": 34.0,
        "rating": 4.7,
        "emoji": "☕",
        "signals": ["views", "trending"],
    },
    {
        "product_id": "camera-battery",
        "name": "Summit X2 Spare Battery",
        "category": "Camera gear",
        "price": 59.0,
        "rating": 4.8,
        "emoji": "🔋",
        "signals": ["views"],
    },
)

pool: ConnectionPool | None = None
secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
jwks_client = PyJWKClient(
    f"{COGNITO_ISSUER}/.well-known/jwks.json",
    cache_jwk_set=True,
    lifespan=3600,
)
recommendation_cache: dict[tuple[str, int], tuple[float, list[dict[str, Any]]]] = {}
recommendation_cache_lock = threading.Lock()
CACHE_TTL_SECONDS = 300
CACHE_MAX_ENTRIES = 5000
order_webhook_secret: str | None = None


def read_secret(secret_arn: str) -> dict[str, str]:
    response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError(f"Expected a SecretString for {secret_arn}")
    value = json.loads(secret_string)
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {secret_arn}")
    return value


def connection_string(credentials: dict[str, str]) -> str:
    return make_conninfo(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=credentials["username"],
        password=credentials["password"],
        sslmode="verify-full",
        sslrootcert="/etc/pki/tls/certs/ca-bundle.crt",
        connect_timeout=5,
    )


def provision_application_role(admin: Connection, app_credentials: dict[str, str]) -> None:
    username = app_credentials["username"]
    with admin.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(1095781459)")
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_roles WHERE rolname = {}").format(
                sql.Literal(username)
            )
        )
        role_exists = cursor.fetchone() is not None
        if role_exists:
            cursor.execute(
                sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(username),
                    sql.Literal(app_credentials["password"]),
                )
            )
        else:
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(username),
                    sql.Literal(app_credentials["password"]),
                )
            )
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(DB_NAME), sql.Identifier(username)
            )
        )
        cursor.execute(
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
                sql.Identifier(username)
            )
        )
        cursor.execute("SELECT pg_advisory_unlock(1095781459)")
    admin.commit()


def initialize_database(connection: Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(1095781460)")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
                rating NUMERIC(2, 1) NOT NULL,
                emoji TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_events (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                customer_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK (
                    event_type IN (
                        'product_view', 'search', 'purchase',
                        'recommendation_impression', 'recommendation_click'
                    )
                ),
                product_id TEXT REFERENCES products(product_id),
                query TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS customer_events_customer_time_idx
            ON customer_events (customer_id, created_at DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS customer_events_time_type_idx
            ON customer_events (created_at DESC, event_type)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_requests (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                customer_id TEXT NOT NULL,
                model_latency_ms INTEGER NOT NULL,
                cache_hit BOOLEAN NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_rate_limits (
                customer_id TEXT NOT NULL,
                window_start TIMESTAMPTZ NOT NULL,
                request_count INTEGER NOT NULL CHECK (request_count BETWEEN 1 AND 8),
                PRIMARY KEY (customer_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_webhook_events (
                event_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL UNIQUE,
                customer_id TEXT NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL,
                payload_sha256 TEXT NOT NULL,
                received_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_webhook_items (
                event_id TEXT NOT NULL REFERENCES order_webhook_events(event_id),
                product_id TEXT NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 99),
                PRIMARY KEY (event_id, product_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS recommendation_requests_customer_time_idx
            ON recommendation_requests (customer_id, created_at DESC)
            """
        )
        cursor.executemany(
            """
            INSERT INTO products (product_id, name, category, price, rating, emoji)
            VALUES (%(product_id)s, %(name)s, %(category)s, %(price)s, %(rating)s, %(emoji)s)
            ON CONFLICT (product_id) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                price = EXCLUDED.price,
                rating = EXCLUDED.rating,
                emoji = EXCLUDED.emoji,
                updated_at = now()
            """,
            PRODUCTS,
        )
        cursor.execute("SELECT pg_advisory_unlock(1095781460)")
    connection.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global order_webhook_secret, pool
    if ORDER_WEBHOOK_SECRET_ARN:
        webhook_secret = read_secret(ORDER_WEBHOOK_SECRET_ARN).get("webhook_secret")
        if not webhook_secret:
            raise RuntimeError(
                "ORDER_WEBHOOK_SECRET_ARN must contain a JSON webhook_secret value."
            )
        order_webhook_secret = webhook_secret
    master = read_secret(DB_MASTER_SECRET_ARN)
    application = read_secret(DB_APP_SECRET_ARN)
    admin_pool = ConnectionPool(
        conninfo=connection_string(master),
        min_size=1,
        max_size=2,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    admin_pool.open(wait=True, timeout=30)
    with admin_pool.connection() as admin:
        provision_application_role(admin, application)
    admin_pool.close()

    pool = ConnectionPool(
        conninfo=connection_string(application),
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    pool.open(wait=True, timeout=30)
    with pool.connection() as connection:
        initialize_database(connection)
    logger.info("Database initialized; application is ready")
    yield
    if pool:
        pool.close()


app = FastAPI(title="Northstar Commerce API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class EventType(StrEnum):
    product_view = "product_view"
    search = "search"
    recommendation_impression = "recommendation_impression"
    recommendation_click = "recommendation_click"


PRODUCT_EVENT_TYPES = {
    EventType.product_view,
    EventType.recommendation_impression,
    EventType.recommendation_click,
}


class CustomerEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    product_id: str | None = Field(default=None, max_length=64)
    query: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_event_context(self) -> CustomerEvent:
        if self.event_type in PRODUCT_EVENT_TYPES and not self.product_id:
            raise ValueError("product_id is required for this event")
        if self.event_type == EventType.search and not self.query:
            raise ValueError("query is required for search events")
        if self.event_type != EventType.search and self.query is not None:
            raise ValueError("query is only allowed for search events")
        return self


def require_customer(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to use the commerce API.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            options={"verify_aud": False, "require": ["exp", "iat", "sub"]},
        )
    except (jwt.PyJWTError, jwt.PyJWKClientError) as error:
        logger.info("Rejected invalid Cognito access token: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or expired. Sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    if (
        claims.get("token_use") != "access"
        or claims.get("client_id") != COGNITO_APP_CLIENT_ID
        or not isinstance(claims.get("sub"), str)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is not authorized for this application.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


def db_pool() -> ConnectionPool:
    if pool is None:
        raise HTTPException(status_code=503, detail="Database is not ready.")
    return pool


AuthenticatedCustomer = Annotated[dict[str, Any], Depends(require_customer)]


def record_customer_event(
    customer_id: str, event: CustomerEvent, connection_pool: ConnectionPool
) -> int:
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        if event.product_id:
            cursor.execute(
                "SELECT 1 FROM products WHERE product_id = %s",
                (event.product_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=422, detail="Unknown product_id.")
        cursor.execute(
            """
            INSERT INTO customer_events (customer_id, event_type, product_id, query)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (customer_id, event.event_type.value, event.product_id, event.query),
        )
        event_id = cursor.fetchone()["id"]
        connection.commit()
    return event_id


def publish_event_metric(event: CustomerEvent, event_id: int) -> bool:
    return publish_event_metric_values(event.event_type.value, event.product_id, event_id)


def publish_event_metric_values(
    event_type: str,
    product_id: str | None,
    event_id: int,
    occurred_at: datetime | None = None,
) -> bool:
    payload = {
        "event_id": event_id,
        "event_type": event_type,
        "product_id": product_id,
        "occurred_at": (occurred_at or datetime.now(UTC)).isoformat(),
    }
    try:
        response = lambda_client.invoke(
            FunctionName=METRICS_LAMBDA_ARN,
            InvocationType="Event",
            Payload=json.dumps(payload).encode("utf-8"),
        )
    except (BotoCoreError, ClientError):
        logger.exception("Customer event %s was saved but its metric was not queued.", event_id)
        return False
    if response.get("StatusCode") != 202:
        logger.error("Customer event %s was saved but its metric was not queued.", event_id)
        return False
    return True


@app.get("/api/health")
def health(connection_pool: Annotated[ConnectionPool, Depends(db_pool)]) -> dict[str, str]:
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok"}


STORE_SESSION_COOKIE = "northstar_store_session"
STORE_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{40,128}$")


def require_store_session(request: Request) -> str:
    session_id = request.cookies.get(STORE_SESSION_COOKIE, "")
    if not STORE_SESSION_PATTERN.fullmatch(session_id):
        raise HTTPException(
            status_code=401,
            detail="Start a storefront session before sending customer activity.",
        )
    return f"store:{session_id}"


StoreCustomer = Annotated[str, Depends(require_store_session)]


class OrderLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=99)


class TrustedOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1, max_length=128)
    session_id: str | None = Field(default=None, min_length=40, max_length=128)
    occurred_at: datetime
    items: list[OrderLine] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_order(self) -> TrustedOrder:
        if self.session_id is not None and not STORE_SESSION_PATTERN.fullmatch(self.session_id):
            raise ValueError("session_id is invalid")
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Order product IDs must be unique.")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include a timezone.")
        return self


def enforce_store_recommendation_limit(
    customer_id: str, connection_pool: ConnectionPool
) -> None:
    window_start = datetime.now(UTC).replace(second=0, microsecond=0)
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO recommendation_rate_limits (customer_id, window_start, request_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (customer_id) DO UPDATE
            SET window_start = EXCLUDED.window_start,
                request_count = CASE
                    WHEN recommendation_rate_limits.window_start = EXCLUDED.window_start
                    THEN recommendation_rate_limits.request_count + 1
                    ELSE 1
                END
            WHERE recommendation_rate_limits.window_start <> EXCLUDED.window_start
               OR recommendation_rate_limits.request_count < 8
            RETURNING request_count
            """,
            (customer_id, window_start),
        )
        if cursor.fetchone() is None:
            connection.rollback()
            raise HTTPException(
                status_code=429,
                detail="Too many recommendation requests. Please try again shortly.",
                headers={"Retry-After": "60"},
            )
        connection.commit()


def get_recommendations(
    customer_id: str,
    request: Request,
    connection_pool: ConnectionPool,
) -> dict[str, Any]:
    started = time.perf_counter()
    newest_event_id, history, products = read_customer_context(customer_id, connection_pool)
    cache_key = (customer_id, newest_event_id)
    now = time.monotonic()
    with recommendation_cache_lock:
        cached = recommendation_cache.get(cache_key)
        cache_hit = cached is not None and cached[0] > now
    if cache_hit:
        items = cached[1]
    else:
        if history:
            items = generate_recommendations(history, products)
        else:
            items = [
                {
                    **product,
                    "reason": "A highly rated pick from our catalog.",
                    "score": round(float(product["rating"]) / 5, 2),
                }
                for product in sorted(
                    products, key=lambda product: float(product["rating"]), reverse=True
                )[:4]
            ]
        with recommendation_cache_lock:
            if len(recommendation_cache) >= CACHE_MAX_ENTRIES:
                oldest_key = min(
                    recommendation_cache,
                    key=lambda key: recommendation_cache[key][0],
                )
                del recommendation_cache[oldest_key]
            recommendation_cache[cache_key] = (now + CACHE_TTL_SECONDS, items)
    duration_ms = round((time.perf_counter() - started) * 1000)
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO recommendation_requests (customer_id, model_latency_ms, cache_hit)
            VALUES (%s, %s, %s)
            """,
            (customer_id, duration_ms, cache_hit),
        )
        connection.commit()
    logger.info(
        "Generated recommendations cache_hit=%s latency_ms=%s",
        cache_hit,
        duration_ms,
        extra={"request_id": request.headers.get("x-amzn-trace-id")},
    )
    return {"items": items, "cache_hit": cache_hit, "latency_ms": duration_ms}


@app.post("/api/store/session")
def create_store_session(response: Response) -> dict[str, bool]:
    session_id = secrets.token_urlsafe(32)
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        STORE_SESSION_COOKIE,
        session_id,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=os.environ.get("STORE_SESSION_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )
    return {"created": True}


@app.get("/api/store/catalog")
def store_catalog(
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, list[dict[str, Any]]]:
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT product_id, name, category, price, rating, emoji
            FROM products
            ORDER BY product_id
            """
        )
        products = cursor.fetchall()
    return {
        "items": [
            {
                **product,
                "price": float(product["price"]),
                "rating": float(product["rating"]),
            }
            for product in products
        ]
    }


@app.post("/api/store/events", status_code=status.HTTP_202_ACCEPTED)
def create_store_event(
    event: CustomerEvent,
    customer_id: StoreCustomer,
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, int | bool]:
    event_id = record_customer_event(customer_id, event, connection_pool)
    metrics_queued = publish_event_metric(event, event_id)
    return {"event_id": event_id, "metrics_queued": metrics_queued}


@app.get("/api/store/recommendations")
def store_recommendations(
    request: Request,
    response: Response,
    customer_id: StoreCustomer,
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "private, no-store"
    enforce_store_recommendation_limit(customer_id, connection_pool)
    return get_recommendations(customer_id, request, connection_pool)


@app.post("/api/webhooks/orders")
async def ingest_order_webhook(
    request: Request,
    event_id: Annotated[str, Header(alias="X-Webhook-Event-Id")],
    timestamp: Annotated[str, Header(alias="X-Webhook-Timestamp")],
    signature: Annotated[str, Header(alias="X-Webhook-Signature")],
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, bool]:
    if not order_webhook_secret:
        raise HTTPException(status_code=503, detail="Order webhook integration is not configured.")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", event_id):
        raise HTTPException(status_code=400, detail="Webhook event ID is invalid.")
    if not re.fullmatch(r"[0-9]{10}", timestamp):
        raise HTTPException(status_code=400, detail="Webhook timestamp is invalid.")
    try:
        timestamp_seconds = int(timestamp)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Webhook timestamp is invalid.") from error
    if abs(time.time() - timestamp_seconds) > 300:
        raise HTTPException(status_code=401, detail="Webhook timestamp is outside the allowed window.")
    body = await request.body()
    if len(body) > 65536:
        raise HTTPException(status_code=413, detail="Webhook payload is too large.")
    expected = "sha256=" + hmac.new(
        order_webhook_secret.encode("utf-8"),
        timestamp.encode("ascii") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Webhook signature is invalid.")
    try:
        order = TrustedOrder.model_validate_json(body)
    except ValidationError as error:
        logger.info("Rejected invalid trusted-order payload.")
        raise HTTPException(status_code=422, detail="Order payload is invalid.") from error
    now = datetime.now(UTC)
    occurred_at = order.occurred_at.astimezone(UTC)
    if occurred_at > now + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Order occurred_at cannot be in the future.")
    customer_id = f"store:{order.session_id}" if order.session_id else f"order:{order.order_id}"
    canonical_payload = json.dumps(
        order.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload_sha256 = hashlib.sha256(canonical_payload).hexdigest()

    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT product_id FROM products WHERE product_id = ANY(%s)", (
            [item.product_id for item in order.items],
        ))
        known_products = {row["product_id"] for row in cursor.fetchall()}
        if known_products != {item.product_id for item in order.items}:
            raise HTTPException(status_code=422, detail="Order contains an unknown product.")
        cursor.execute(
            """
            INSERT INTO order_webhook_events (
                event_id, order_id, customer_id, occurred_at, payload_sha256
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING event_id
            """,
            (
                event_id,
                order.order_id,
                customer_id,
                occurred_at,
                payload_sha256,
            ),
        )
        inserted = cursor.fetchone() is not None
        if not inserted:
            cursor.execute(
                """
                SELECT event_id, payload_sha256 FROM order_webhook_events
                WHERE event_id = %s OR order_id = %s
                """,
                (event_id, order.order_id),
            )
            prior = cursor.fetchone()
            if (
                not prior
                or prior["event_id"] != event_id
                or not hmac.compare_digest(prior["payload_sha256"], payload_sha256)
            ):
                connection.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Webhook event ID was already used with a different order payload.",
                )
            connection.rollback()
            return {"accepted": True, "duplicate": True}
        purchase_event_ids: list[int] = []
        for item in order.items:
            cursor.execute(
                """
                INSERT INTO order_webhook_items (event_id, product_id, quantity)
                VALUES (%s, %s, %s)
                """,
                (event_id, item.product_id, item.quantity),
            )
            cursor.execute(
                """
                INSERT INTO customer_events (customer_id, event_type, product_id, created_at)
                VALUES (%s, 'purchase', %s, %s)
                RETURNING id
                """,
                (customer_id, item.product_id, occurred_at),
            )
            purchase_event_ids.append(cursor.fetchone()["id"])
        connection.commit()
    queued = [
        publish_event_metric_values(
            "purchase", item.product_id, purchase_event_id, occurred_at
        )
        for item, purchase_event_id in zip(order.items, purchase_event_ids)
    ]
    metrics_queued = all(queued)
    return {"accepted": True, "duplicate": False, "metrics_queued": metrics_queued}


@app.post("/api/events", status_code=status.HTTP_202_ACCEPTED)
def create_event(
    event: CustomerEvent,
    claims: AuthenticatedCustomer,
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, int | bool]:
    event_id = record_customer_event(claims["sub"], event, connection_pool)
    metrics_queued = publish_event_metric(event, event_id)
    return {"event_id": event_id, "metrics_queued": metrics_queued}


def read_customer_context(
    customer_id: str, connection_pool: ConnectionPool
) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, event_type, product_id, query, created_at,
                   max(id) OVER () AS newest_event_id
            FROM customer_events
            WHERE customer_id = %s
              AND event_type IN ('product_view', 'search', 'purchase')
            ORDER BY created_at DESC, id DESC
            LIMIT 30
            """,
            (customer_id,),
        )
        history = cursor.fetchall()
        cursor.execute(
            """
            SELECT product_id, name, category, price, rating
            FROM products
            ORDER BY product_id
            """
        )
        products = cursor.fetchall()
    newest_event_id = history[0]["newest_event_id"] if history else 0
    return newest_event_id, history, products


def generate_recommendations(
    history: list[dict[str, Any]], products: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    prompt = {
        "customer_history": [
            {
                "type": row["event_type"],
                "product_id": row["product_id"],
                "search": row["query"],
                "occurred_at": row["created_at"].isoformat(),
            }
            for row in history
        ],
        "available_catalog": [
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "price": float(product["price"]),
                "rating": float(product["rating"]),
            }
            for product in products
        ],
    }
    try:
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[
                {
                    "text": (
                        "Recommend only product IDs in the supplied catalog. Use the customer's "
                        "recent actions to explain why each item is relevant. Return strict JSON "
                        'only in this shape: {"recommendations":[{"product_id":"...","reason":"...","score":0.0}]}. '
                        "Return up to eight unique catalog products, aiming for eight when the catalog "
                        "has enough candidates. Never invent a product."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": json.dumps(prompt, ensure_ascii=False)}],
                }
            ],
            inferenceConfig={"maxTokens": 1400, "temperature": 0.2},
        )
    except ClientError as error:
        logger.exception("Amazon Bedrock recommendation request failed.")
        raise HTTPException(
            status_code=502,
            detail="The recommendation service is temporarily unavailable.",
        ) from error
    blocks = response.get("output", {}).get("message", {}).get("content", [])
    text = next((block["text"] for block in blocks if "text" in block), None)
    if not text:
        raise HTTPException(status_code=502, detail="Bedrock returned no recommendation text.")
    try:
        body = json.loads(text)
    except json.JSONDecodeError as error:
        logger.error("Bedrock returned invalid JSON for a recommendation response.")
        raise HTTPException(status_code=502, detail="Bedrock returned invalid recommendation JSON.") from error
    items = body.get("recommendations") if isinstance(body, dict) else None
    products_by_id = {product["product_id"]: product for product in products}
    if not isinstance(items, list):
        raise HTTPException(status_code=502, detail="Bedrock response is missing recommendations.")

    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        product_id = item.get("product_id")
        reason = item.get("reason")
        score = item.get("score")
        if (
            product_id not in products_by_id
            or product_id in seen
            or not isinstance(reason, str)
            or not reason.strip()
            or not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not 0 <= score <= 1
        ):
            continue
        validated.append(
            {
                **products_by_id[product_id],
                "reason": reason.strip()[:240],
                "score": round(float(score), 2),
            }
        )
        seen.add(product_id)
    if not validated:
        raise HTTPException(
            status_code=502,
            detail="Bedrock did not return any valid products from the catalog.",
        )
    return validated


@app.get("/api/recommendations")
def recommendations(
    request: Request,
    claims: AuthenticatedCustomer,
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
) -> dict[str, Any]:
    return get_recommendations(claims["sub"], request, connection_pool)


@app.get("/api/summary")
def summary(
    claims: AuthenticatedCustomer,
    connection_pool: Annotated[ConnectionPool, Depends(db_pool)],
    days: Annotated[int, Query(ge=7, le=30)] = 7,
) -> dict[str, Any]:
    if "store-admins" not in claims.get("cognito:groups", []):
        raise HTTPException(
            status_code=403,
            detail="Only authorized store administrators can view aggregate analytics.",
        )
    if days not in (7, 30):
        raise HTTPException(status_code=422, detail="Choose a 7-day or 30-day activity range.")
    now = datetime.now(UTC)
    cutoff_7d = now - timedelta(days=7)
    activity_cutoff = now - timedelta(days=days)
    with connection_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                count(*) FILTER (WHERE created_at >= %s) AS events_7d,
                count(*) FILTER (WHERE event_type = 'product_view' AND created_at >= %s) AS views_7d,
                count(*) FILTER (WHERE event_type = 'purchase' AND created_at >= %s) AS purchases_7d,
                count(*) FILTER (WHERE event_type = 'recommendation_impression' AND created_at >= %s) AS impressions_7d,
                count(*) FILTER (WHERE event_type = 'recommendation_click' AND created_at >= %s) AS clicks_7d
            FROM customer_events
            """,
            (cutoff_7d, cutoff_7d, cutoff_7d, cutoff_7d, cutoff_7d),
        )
        totals = cursor.fetchone()
        bucket = "day" if days == 7 else "week"
        cursor.execute(
            """
            SELECT date_trunc(%s, created_at)::date AS day,
                   count(*) FILTER (WHERE event_type = 'product_view') AS views,
                   count(*) FILTER (WHERE event_type = 'purchase') AS purchases
            FROM customer_events
            WHERE created_at >= %s
            GROUP BY day
            ORDER BY day
            """,
            (bucket, activity_cutoff),
        )
        activity = cursor.fetchall()
        cursor.execute(
            """
            SELECT p.category, count(*) AS views
            FROM customer_events e
            JOIN products p ON p.product_id = e.product_id
            WHERE e.event_type = 'product_view'
              AND e.created_at >= %s
            GROUP BY p.category
            ORDER BY views DESC
            LIMIT 1
            """,
            (cutoff_7d,),
        )
        top_category = cursor.fetchone()
        cursor.execute(
            """
            SELECT p.category,
                   count(*) FILTER (WHERE e.created_at >= %s) AS views_7d,
                   count(*) FILTER (
                       WHERE e.created_at >= %s AND e.created_at < %s
                   ) AS views_previous_7d
            FROM customer_events e
            JOIN products p ON p.product_id = e.product_id
            WHERE e.event_type = 'product_view'
              AND e.created_at >= %s
            GROUP BY p.category
            HAVING count(*) FILTER (WHERE e.created_at >= %s) > 0
            ORDER BY views_7d DESC
            LIMIT 4
            """,
            (
                cutoff_7d,
                cutoff_7d - timedelta(days=7),
                cutoff_7d,
                cutoff_7d - timedelta(days=7),
                cutoff_7d,
            ),
        )
        category_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT coalesce(round(avg(model_latency_ms))::int, 0) AS avg_latency_ms,
                   coalesce(round(100.0 * count(*) FILTER (WHERE cache_hit) /
                                  nullif(count(*), 0), 0), 0) AS cache_hit_percent
            FROM recommendation_requests
            WHERE created_at >= %s
            """,
            (cutoff_7d,),
        )
        performance = cursor.fetchone()
        cursor.execute("SELECT count(*) AS product_count FROM products")
        product_count = cursor.fetchone()["product_count"]
        cursor.execute(
            """
            SELECT e.event_type, p.name AS product_name, e.query, e.created_at
            FROM customer_events e
            LEFT JOIN products p ON p.product_id = e.product_id
            ORDER BY e.id DESC
            LIMIT 4
            """
        )
        recent_events = cursor.fetchall()

    ctr = (
        round(100 * totals["clicks_7d"] / totals["impressions_7d"], 2)
        if totals["impressions_7d"]
        else 0
    )
    return {
        "events_7d": totals["events_7d"],
        "views_7d": totals["views_7d"],
        "purchases_7d": totals["purchases_7d"],
        "impressions_7d": totals["impressions_7d"],
        "clicks_7d": totals["clicks_7d"],
        "ctr_percent": ctr,
        "top_category": top_category["category"] if top_category else None,
        "trending_categories": [
            {
                "category": row["category"],
                "views_7d": row["views_7d"],
                "growth_percent": (
                    round(100 * (row["views_7d"] - row["views_previous_7d"]) / row["views_previous_7d"])
                    if row["views_previous_7d"]
                    else None
                ),
            }
            for row in category_rows
        ],
        "product_count": product_count,
        "avg_latency_ms": performance["avg_latency_ms"],
        "cache_hit_percent": performance["cache_hit_percent"],
        "activity_days": days,
        "activity": [
            {
                "day": row["day"].isoformat(),
                "views": row["views"],
                "purchases": row["purchases"],
            }
            for row in activity
        ],
        "recent_events": [
            {
                "event_type": row["event_type"],
                "product_name": row["product_name"],
                "query": row["query"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in recent_events
        ],
    }


web_directory = os.environ.get("WEB_DIRECTORY", "/opt/northstar/web")
if os.path.isdir(web_directory):
    app.mount("/", StaticFiles(directory=web_directory, html=True), name="web")
