class BaseGateway:
    """Base for outbound business capability ports.

    Gateways are core-facing interfaces to external systems. A gateway should
    expose business language, not SDK, HTTP, queue, or vendor details.

    Example:
        EmailGateway sends transactional emails.
    """
