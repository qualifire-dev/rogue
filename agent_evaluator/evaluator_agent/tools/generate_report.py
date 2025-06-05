import json


def generate_report(scenarios, test_cases, evaluations, failures):
    """
    Generates a report for the evaluated agent.
    :param scenarios: A list of tested scenarios.
    :param test_cases: All the test cases executed for all the scenarios.
    :param evaluations: The results of each test case evaluation.
    :param failures:
    :return:
    """
    return json.dumps(
        {
            "scenarios": scenarios,
            "test_cases": test_cases,
            "evaluations": evaluations,
            "failures": failures,
        },
        indent=2,
    )
