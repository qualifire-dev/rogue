import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
)


from .tshirt_store_agent import agent as root_agent
