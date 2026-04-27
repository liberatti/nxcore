from pathlib import Path

from setuptools import setup, find_packages

this_dir = Path(__file__).parent
readme = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="nxcore",
    version="v1.0.0",
    author="Gustavo Liberatti",
    author_email="liberatti.gustavo@gmail.com",
    description="Internal library for use in private projects.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/liberatti/nxcore",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.33.1",
        "pytz>=2025.1",
        "flask>=3.1.3",
        "PyJWT>=2.12.1",
        "marshmallow>=4.3.0",
        "bson"
    ],
    extras_require={
        "web": [
            "flask-socketio>=5.6.0",
            "eventlet>=0.40.4",
        ],
        "oracle": ["cx_Oracle~=8.3.0"],
        "mongo": ["pymongo>=4.17.0"],
        "sqlite": [],
        "redis": ["redis"],
        "rabbitmq": ["pika>=1.3.2"],
        "minio": ["minio>=7.2.20"],
        "image": [
            "numpy>=2.4.4",
            "opencv-python>=4.13.0.92",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
