def acceptance_probe():
    checkpoint = 40
    result = checkpoint + 2
    print("ACCEPTANCE_RUN", result)
    return result

acceptance_result = acceptance_probe()

def acceptance_failure():
    pm_value = 73
    raise RuntimeError("ACCEPTANCE_PM")

acceptance_failure()
