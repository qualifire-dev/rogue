import setuptools

with open("requirements.txt", "r") as f:
    requirements = [line for line in f.read().splitlines()]


setuptools.setup(
    name="rogue",
    version="0.0.1",
    description="Rogue agent evaluator",
    python_requires=">=3.11",
    install_requires=requirements,
)
