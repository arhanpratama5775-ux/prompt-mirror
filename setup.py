from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="prompt-mirror",
    version="0.3.0",
    author="Titizzz",
    description="A digital mirror for your AI conversations - analyze patterns, generate insights",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arhanpratama5775-ux/prompt-mirror",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Utilities",
    ],
    keywords="ai, chatgpt, claude, gemini, conversation-analysis, self-improvement, reflection",
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0,<9.0.0",
        "rich>=13.0.0,<14.0.0",
    ],
    extras_require={
        # Support both 'viz' (as documented in README) and 'visualize'
        "viz": [
            "matplotlib>=3.5.0,<4.0.0",
        ],
        "visualize": [
            "matplotlib>=3.5.0,<4.0.0",
        ],
        "pdf": [
            "reportlab>=3.6.0,<5.0.0",
        ],
        "all": [
            "matplotlib>=3.5.0,<4.0.0",
            "reportlab>=3.6.0,<5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "prompt-mirror=prompt_mirror.cli:main",
        ],
    },
)
