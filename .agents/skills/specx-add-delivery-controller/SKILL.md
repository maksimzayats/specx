---
name: specx-add-delivery-controller
description: Add delivery controllers for Specx services, especially FastAPI HTTP routes. Use when creating top-level `delivery/` request/response schemas, one controller per scoped use-case set, route registration, FastAPI lifecycle managers, HTTP error translation, delivery-only auth/rate-limit/request services, or integration tests that exercise the delivery edge.
---

# Specx Add Delivery Controller

Use this skill at the framework boundary. Read `references/controller.md`
before adding controller code.

## Workflow

1. Put controllers under `delivery/fastapi/controllers/<scope>.py`.
2. Put request and response schemas under `delivery/fastapi/schemas/`.
3. Use one controller per scoped set of use cases, for example
   `TasksController` for create/get/list task routes.
4. Put controller-only helpers such as auth dependencies, rate limiters, and
   request-context readers under `delivery/fastapi/services/`.
5. Make controllers inherit `BaseController`, schemas inherit
   `BaseFastAPISchema`, delivery helpers inherit `BaseDeliveryService`, and
   FastAPI lifespan managers inherit `BaseLifecycle[FastAPI]`.
6. Add docstrings with scope and a concrete `Example:` to controllers, schemas,
   and delivery services.
7. Inject use cases or delivery services with `Injected[...]`. Operational
   probe controllers inject the reusable `core/health` probe use cases.
8. Map request schema/path data into the use case's same-file `Command` or
   `Query` input.
9. Call the use case.
10. Map the result into a response schema.
11. Translate known application exceptions into HTTP responses.
12. Register full public business route paths such as `/api/v1/users`. Do not
   split API prefixes across routers and route fragments. Operational probes
   are the only unversioned exception: `/healthz` and `/readyz`.
13. For FastAPI apps with long-lived resources, inject `FastAPILifecycle` into
   the app factory and pass it to `FastAPI(lifespan=...)`.
14. Add integration tests at the HTTP boundary.

## Code Style

Use blank lines as logical separators in all code. Keep related statements
together, but separate independent setup, action, assertion, response, branch,
and transformation groups so long blocks stay readable.

## References

- `references/controller.md` - FastAPI controller class pattern, app factory
  registration, schemas, and tests.
