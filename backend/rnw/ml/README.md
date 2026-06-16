# RNW ML Layer

The current recommendation system is an explainable scoring engine in `rnw/services/recommendation_service.py`. This folder is reserved for a future trained model.

Suggested evolution:

1. Export interaction data from `search_history`, `saved_properties`, `rental_applications`, and `properties`.
2. Train a ranking model that predicts application/save probability.
3. Store the model in this folder or in object storage.
4. Replace or blend the transparent score with model probability.
