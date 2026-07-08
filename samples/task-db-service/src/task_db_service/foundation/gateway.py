class BaseGateway:
    """Base class for outbound business capabilities.

    Gateways are core-facing interfaces to external systems. A gateway should
    expose business language, not SDK or HTTP details.

    Example:
        TaskSummaryGateway generates summaries for task descriptions.
        PaymentGateway charges customers.
        EmailGateway sends transactional emails.
    """
