class BaseCapability:
    """Base for small injectable collaborators narrower than services.

    Capabilities do one focused thing, may be injected or faked, and do not own
    application workflows, unit-of-work scopes, repositories, or gateways.

    Example:
        SlugGeneratingCapability creates slugs for display labels.
    """
