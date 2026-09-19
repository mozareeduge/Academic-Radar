class CanaryNotDetected(AssertionError):
    pass


def expect_violation(check, *args, **kwargs):
    try:
        check(*args, **kwargs)
    except AssertionError:
        return None
    raise CanaryNotDetected(f'canary not detected: {check.__name__}')
