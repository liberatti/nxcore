# nxcore

[![Version](https://img.shields.io/badge/version-v0.0.7-blue.svg)](https://github.com/liberatti/nxcore)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Internal Python library designed to provide common and reusable functionalities for private web projects. It streamlines development by offering a robust set of tools for authentication, database integration, messaging, and AI-powered tasks.

## 🚀 Key Features

- **🔐 Auth & Security**: Full JWT integration for authentication and authority-based authorization.
- **🍃 MongoDB Integration**: Simplified DAO (Data Access Object) with built-in pagination and schema validation.
- **🐰 RabbitMQ & Messaging**: Easy-to-use wrappers for asynchronous task handling.
- **📦 Cloud Storage**: Seamless integration with MinIO for object storage.
- **🛡️ OAuth Support**: Pre-configured handlers for Google and Microsoft authentication.
- **👁️ Computer Vision**: Facial recognition powered by DeepFace and advanced image processing utilities.
- **🛠️ Common Utilities**: A collection of helpers for deep merging, date formatting, and more.

## 🛠️ Installation

Install the library in editable mode for development:

```bash
pip install -e . --break-system-packages
```

To install specific extras:

```bash
pip install "nxcore[web,mongo,image]"
```

## 📖 Quick Start

### Basic Controller & Auth

```python
from nxcore.controllers.base_controller import has_any_authority, response_data

@has_any_authority(["ROLE_ADMIN"])
def get_user_profile(user_id):
    # Logic to fetch user
    user = {"id": user_id, "name": "John Doe"}
    return response_data(user)
```

### MongoDB DAO

```python
from nxcore.repository.mongo import MongoDAO

class UserDAO(MongoDAO):
    def __init__(self, url):
        super().__init__(url, collection_name="users")

with UserDAO(mongo_url) as dao:
    users = dao.get_all(pagination={"page": 1, "per_page": 10})
```

## 📂 Project Structure

- `nxcore/controllers/`: Base controllers and response helpers.
- `nxcore/middleware/`: JWT handling, logging, and socket management.
- `nxcore/repository/`: Data access tools for MongoDB, RabbitMQ, and MinIO.
- `nxcore/tools/`: Integration with OAuth providers, DeepFace, and image processing.
- `nxcore/common_utils.py`: General purpose utility functions.
- `nxcore/config.py`: Centralized configuration management.

## 🤝 Contribution

This is an internal library. For contributions, please follow the internal development workflow:
1. Create a feature branch.
2. Ensure all methods are documented.
3. Submit a Pull Request.

## ✍️ Author

**Gustavo Liberatti**
- Email: [liberatti.gustavo@gmail.com](mailto:liberatti.gustavo@gmail.com)
- GitHub: [@liberatti](https://github.com/liberatti)

## 📜 License

Distributed under the Apache License 2.0. See `LICENSE` for more information.