class BaseCapability:
    """Base class for small injectable collaborators.

    Capabilities do one narrow thing, may be injected or faked, and do not own
    application workflows, unit-of-work scopes, repositories, or gateways.

    Example:
        SlugGeneratingCapability creates slugs for display labels.
        BaseClock can be introduced later for concrete clocks such as SystemClock.
        BaseGenerator can be introduced later for classes such as UUID7Generator.
    """
