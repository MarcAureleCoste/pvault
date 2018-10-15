# pvault
Python web application to manage your password


## Getting Started

1. Change directory into your newly created project.

    ```bash
    cd pvault
    ```

2. Create a Python virtual environment.

    ```bash
    python3 -m venv env
    ```

- Upgrade packaging tools.

    ```bash
    env/bin/pip install --upgrade pip setuptools
    ```

- Install the project in editable mode with its testing requirements.

    ```bash
    env/bin/pip install -e ".[testing]"
    ```

- Run your project's tests.

    ```bash
    env/bin/pytest
    ```

- Run your project.

    ```bash
    env/bin/pserve development.ini
    ```
