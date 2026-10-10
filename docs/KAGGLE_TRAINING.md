# Kaggle data and model run

## Dataset to download

Use the **Event-Driven Trading (EDT)** benchmark released with the Trade the Event research project. The benchmark has 303,893 timestamped news articles and attached one-, two-, and three-day stock price labels. The dataset card reports 1.7 GB for the complete dataset and covers March 2020 to May 2021. The notebook needs only `Trading_benchmark/evaluate_news.json`; skip the domain-adaptation corpus and unrelated files.

- [EDT project and download instructions](https://github.com/Zhihan1996/TradeTheEvent#dataset)
- [EDT dataset folder](https://drive.google.com/drive/folders/1xKjd9hzA8UTn2DXVIYYnX5TngNAMom19?usp=sharing)
- [Dataset card and schema](https://huggingface.co/datasets/agungpambudi/corporate-event-detection)
- [RiskPulse Kaggle notebook](../notebooks/riskpulse_kaggle_embeddings_xgb.ipynb)

The price label is an imperfect proxy: the source assigns tickers automatically and reports false assignments for some unrelated articles. The notebook filters missing prices and requires a ticker or exchange marker in the text. That filter is conservative, but it cannot remove every bad match. Do not describe the output as causal news impact.

## Data volume

The bundled live RSS snapshot has 30 rows. It is far too small to train XGBoost meaningfully.

For the first model run, the notebook uses 50,000 rows from the timestamped benchmark, sorted by publication date. That gives about 40,000 training rows and 10,000 latest-date validation rows. A 384-dimension float16 embedding cache is about 37 MiB before compression. The benchmark's full 303,893 rows are a later option; their float16 vectors are about 223 MiB before compression. XGBoost consumes float32 arrays during training, still well within a typical notebook's memory budget at this size.

These are engineering starting points, not guarantees of statistical sufficiency. Look at ticker coverage, duplicates, price-label quality, and the held-out error before keeping the model.

## Kaggle steps

1. Import the RiskPulse notebook file into Kaggle. With Internet enabled, it downloads only `Trading_benchmark/evaluate_news.json` from the Hugging Face mirror into `/kaggle/working/data`. Alternatively, add that JSON as a private Kaggle Dataset input; the notebook prefers an attached input when present.
2. Select a GPU accelerator for faster MiniLM embedding generation. Kaggle controls GPU availability and session quotas. XGBoost trains on CPU.
3. Run from the first cell. Embeddings are written in 2,048-row checkpoints under `/kaggle/working`; if the cell stops, rerun it in the same preserved session to continue.
4. When training finishes, download `impact_xgb.json`, `impact_calibration.json`, and optionally `embedding_cache.npz` from the notebook outputs into this repo's `models/` directory. The cache is optional for live inference; this run downloaded it for reproducibility.

Kaggle documents notebook output saving/versioning and GPU session settings in its [Notebooks guide](https://www.kaggle.com/docs/notebooks). Save a notebook version after completion so the model artifacts survive the interactive session.

## What is trained

The notebook runs `all-MiniLM-L6-v2` as a frozen encoder and does not fine-tune it. It trains one XGBoost regressor on CPU (`tree_method='hist'`) to estimate the log of the absolute next-trading-day price move from the 384 embedding values. A held-out latest-date slice is compared with a median baseline. The model does not train an LLM, embedding model, or ensemble stack.

At inference, RiskPulse converts the predicted move to a 1–10 scale using training-set 10th and 90th percentile movement levels. This is a relative ranking proxy for single-stock volatility. Portfolio stress still uses the explicit event shock assumptions in `src/stress/model.py`; it does not feed the XGBoost prediction directly into a loss calculation.
