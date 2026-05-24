# xG90

A modern football data lakehouse that turns raw events into tactical insights. Built with a "Medallion" architecture (Bronze/Silver/Gold) to process StatsBomb data into a premium analytics dashboard.

## Features
- **Automated Pipeline**: End-to-end data flow using **Prefect**.
- **Tactical DNA**: High-level metrics like PPDA and Press Height.
- **Match Momentum**: Cumulative xG charts to see how games evolved.
- **Elite UI**: Custom dark-mode dashboard with Glassmorphism effects.

## Tech Stack
- **Database**: [DuckDB](https://duckdb.org/)
- **Orchestration**: [Prefect](https://www.prefect.io/)
- **Frontend**: [Streamlit](https://streamlit.io/) & [Plotly](https://plotly.com/)
- **Storage**: AWS S3 & Parquet
- **Source**: StatsBomb Open Data

## Setup
1. Fill `.env` with AWS credentials.
2. Run `make install`.
3. Warm up the database: `PYTHONPATH=. python scripts/warm_up_lakehouse.py`.
4. Launch: `make run`.

Built for the love of the game and clean data. ⚽
