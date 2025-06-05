import setuptools

with open("requirements.txt", "r") as f:
    requirements = [line for line in f.read().splitlines()]


setuptools.setup(
    name="agent_evaluator",
    version="0.0.1",
    description="Qualifire Agent Evaluator",
    python_requires=">=3.11",
    install_requires=requirements,
)
