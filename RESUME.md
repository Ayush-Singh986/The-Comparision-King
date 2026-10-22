# Northstar Goods — Resume and Project Impact Guide

## 30-second explanation

Northstar is a cloud e-commerce recommendation project. It records anonymous shopper activity, reads product and behavior data from PostgreSQL, and uses Amazon Bedrock to suggest products from the store's own catalog. A separate trusted order webhook protects purchase events from browser forgery. The AWS architecture is defined in Terraform.

## Resume-ready project entry

**Northstar Goods | Personalized E-commerce Storefront**

*AWS, Terraform, Python, FastAPI, PostgreSQL, Amazon Bedrock, JavaScript*

- Built a storefront API that serves a PostgreSQL-backed catalog, assigns anonymous HTTP-only shopper sessions, and records product views, searches, recommendation impressions, and clicks.
- Implemented contextual Amazon Bedrock recommendations grounded in recent shopper activity and the store catalog, with response validation and a short-lived cache.
- Built a signed, idempotent server-to-server order-event endpoint so purchase analytics depend on trusted order events rather than browser claims.
- Defined a cost-conscious Terraform portfolio deployment with CloudFront/WAF, an Application Load Balancer, EC2 Auto Scaling, private single-AZ RDS PostgreSQL, Cognito, Bedrock, Lambda, and CloudWatch.
- Added CI checks for the backend test suite, Python and JavaScript syntax, and Terraform formatting/validation.

**Impact honesty:** this is an implemented portfolio prototype and AWS reference deployment, not a live commerce service. The AWS stack has not been applied, and there are no production users, controlled experiments, or measured sales, conversion, retention, latency, or cost results. Do not attach business-impact percentages to it yet. The default AWS sizing is cost-conscious for a portfolio demo and intentionally sacrifices multi-AZ failover.

## What problem it addresses

When customers cannot quickly find relevant products, they may abandon a store without buying. Northstar demonstrates a way to make discovery more relevant: capture useful browsing signals, combine them with the store's catalog, and return recommendations that are limited to products the store actually offers.

This demonstrates a potential business benefit—not a proven sales result. The project does not currently have a payment provider, production checkout, inventory service, or a real merchant catalog.

## How the main pieces work

1. **Storefront:** shoppers browse products, search, and open product pages. The bag is stored in the browser; checkout is still a demo.
2. **Anonymous session:** the API issues a random, HTTP-only cookie. Browsers do not choose another customer's server-side identity or submit purchase events.
3. **Catalog and activity:** the storefront reads the catalog through FastAPI. Views, searches, recommendation impressions, and clicks are recorded in PostgreSQL against the session.
4. **Recommendations:** a new session gets top-rated catalog picks without a model call. After activity is available, the API supplies recent events and catalog products to Bedrock, validates the response against known product IDs, and temporarily caches the result.
5. **Trusted orders:** an external server-side order system can send an HMAC-signed event after it verifies an order. The endpoint checks the signature and timestamp, validates product IDs, rejects conflicting replays, and records purchase events transactionally. It does not charge a customer.
6. **Operations:** Cognito protects the separate operations dashboard. Lambda publishes event metrics to CloudWatch; CloudWatch and the load balancer/database provide operational monitoring.
7. **Infrastructure:** Terraform describes the AWS network, edge, compute, database, identity, model access, monitoring, and secrets. CI checks code and Terraform without needing AWS credentials.

## Business impact: what is real vs. what is a goal

### What the prototype demonstrates

- **Personalized discovery flow:** the prototype captures shopper activity and uses it as recommendation context. Whether that improves discovery or sales is untested.
- **Catalog-grounded output:** model responses are checked against the available products before they are returned.
- **Cost-control mechanisms:** first-visit recommendations avoid a model call and repeated results can be cached. Overall savings depend on real traffic and cache-hit rate and have not been measured.
- **Trusted purchase-event design:** the signed server-to-server path can record order events idempotently. No payment provider or real checkout is connected.
- **Cost-aware deployment design:** the defaults use one NAT Gateway, one minimum EC2 instance, and a small single-AZ database to reduce idle baseline costs. This is a design choice, not a measured bill reduction, and it is not the high-availability configuration for production.
- **Operational and deployment design:** Terraform and CloudWatch configuration describe a deployable AWS stack. The stack has not been provisioned or load-tested.

### Measure before claiming commercial results

There is no measured percentage impact to report today. Percentages such as “increased sales by 20%” or “reduced costs by 30%” would be fabricated without live data and a baseline. After a real deployment and checkout integration, compare a randomized recommendation treatment group with a control group. Useful measures include:

| Measure | Example definition | Why it matters |
| --- | --- | --- |
| Recommendation click-through rate | Recommendation clicks ÷ recommendation impressions | Indicates whether shown picks attract interest. |
| Purchase conversion rate | Verified orders ÷ eligible shopper sessions | Connects recommendations to completed orders. |
| Average order value | Verified sales value ÷ verified orders | Shows whether basket value changes. Requires trusted order totals. |
| Recommendation latency | API response-time percentiles | Tracks shopper experience and backend performance. |
| Model/cache efficiency | Bedrock calls, cache-hit rate, and model spend per session | Tests whether caching and the no-history path reduce cost. |
| Reliability | API error rate and successful order-event processing | Checks that browsing and order signals are dependable. |

For measured relative uplift, use:

`relative change (%) = (treatment metric - control metric) / control metric × 100`

Only after measurement, a resume statement could read: “Improved recommendation click-through rate by **X% relative** versus a randomized control across **N** eligible sessions over **T** weeks.” Replace every placeholder with experiment results and identify the observation period. For cost, compare Bedrock spend per eligible session; for latency, report the measured percentile and control comparison. If the project remains undeployed, use concrete implementation scope instead of a business-impact percentage.

## Interview talking points

- **Why send store data to Bedrock?** A general model does not know a merchant's live catalog or a customer's browsing. The application provides both as context and validates suggested product IDs before returning them.
- **How are purchases protected?** The customer-facing event model rejects purchase events. A trusted backend signs the exact request body with HMAC-SHA256; the API checks a short timestamp window and uses database uniqueness/idempotency to make retries safe.
- **How do you control recommendation costs?** New sessions do not invoke the model; repeated results can be cached for five minutes; public recommendation requests have per-session and edge rate limits.
- **What are the trade-offs?** The in-memory cache is per EC2 process rather than shared, session cookies are pseudonymous rather than user accounts, and the webhook is only an ingestion boundary. A payment adapter, inventory, shared cache, consent/retention policy, schema migrations, and production recovery drills remain follow-up work.
- **How was it verified?** The repository has automated API/webhook/model-validation tests plus syntax and Terraform validation checks. AWS provisioning, live integration testing, load testing, and an RDS restore drill have not been performed.

## Useful code pointers

- [Storefront API, event handling, recommendation logic, and order webhook](./backend/app.py)
- [Storefront UI, live catalog integration, and activity capture](./web/store.js)
- [Terraform deployment and AWS resources](./infra/)
- [WAF edge rate limiting](./infra/security.tf)
- [Backend tests](./backend/tests/test_app.py)
- [Continuous integration workflow](./.github/workflows/ci.yml)
- [Full architecture and deployment guide](./README.md)

## Short versions for a resume

**One-line project description:**

Built an AWS/Terraform reference e-commerce storefront that uses shopper activity and a verified product catalog to generate contextual recommendations with Amazon Bedrock.

**Portfolio tagline:**

From anonymous browsing signals to catalog-grounded suggestions—with a trusted order-event boundary and an AWS deployment design.
