name = 'workers'


def task(*arg, **kwarg):
    """
    Need to wrap this task import so it doesnt explode during Django init.

    """
    from .worker import task
    return task(*arg, **kwarg)
