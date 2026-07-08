class BaseUnitOfWork:
    """Base for active transaction objects exposed inside manager scopes.

    Example:
        async with manager as unit_of_work:
            task = await unit_of_work.tasks.get(task_id=1)
    """
