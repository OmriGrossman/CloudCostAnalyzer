import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


# Function to fetch environment variables
def get_env_variable(key):
    """
    Retrieves the value of an environment variable and raises an error if it is not set.

    Args:
        key (str): The name of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not found or is empty.
    """

    value = os.getenv(key)
    if not value:
        raise ValueError(f"Environment variable {key} is missing!")
    return value
