from pymongo import MongoClient
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sys

def clean_title(title):
    title = re.sub("[^a-zA-Z0-9 ]", "", title)
    return title

def create_tfidf_vectorizer(data):
    data["clean_title"] = data["title"].apply(clean_title)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(data["clean_title"])
    return vectorizer, tfidf_matrix

def search(title, vectorizer, tfidf_matrix, data):
    title = clean_title(title)
    query_vec = vectorizer.transform([title])
    similarity = cosine_similarity(query_vec, tfidf_matrix).flatten()
    indices = np.argpartition(similarity, -5)[-5:]
    results = data.iloc[indices].iloc[::-1]
    return results

# Recommendation System
def find_similar_movies(movie_id, data, rating_data):
    similar_users = rating_data[(rating_data["movieId"] == movie_id) & (rating_data["rating"] > 4)]["userId"].unique()
    similar_user_recs = rating_data[(rating_data["userId"].isin(similar_users)) & (rating_data["rating"] > 4)]["movieId"]
    similar_user_recs = similar_user_recs.value_counts() / len(similar_users)

    similar_user_recs = similar_user_recs[similar_user_recs > .10]
    all_users = rating_data[(rating_data["movieId"].isin(similar_user_recs.index)) & (rating_data["rating"] > 4)]
    all_user_recs = all_users["movieId"].value_counts() / len(all_users["userId"].unique())
    rec_percentages = pd.concat([similar_user_recs, all_user_recs], axis=1)
    rec_percentages.columns = ["similar", "all"]

    rec_percentages["score"] = rec_percentages["similar"] / rec_percentages["all"]
    rec_percentages = rec_percentages.sort_values("score", ascending=False)
    return rec_percentages.head(10).merge(data, left_index=True, right_on="movieId")[["score", "title", "genres"]]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python movie_recommendation_script.py <movie_name>")
        sys.exit(1)

    movie_name = sys.argv[1]

    # Connect to MongoDB
    client = MongoClient("mongodb+srv://bvrit-portal:AQPZMWO4tQAvMe9L@cluster0.dmnsn.mongodb.net")
    db = client["ml"]
    
    # Load movies data from MongoDB collection
    movies_collection = db["allmovies"]
    movies_data = list(movies_collection.find())
    movies = pd.DataFrame(movies_data)

    # Load ratings data from MongoDB collection
    ratings_collection = db["allratings"]
    ratings_data = list(ratings_collection.find())
    ratings = pd.DataFrame(ratings_data)

    # Process movie recommendations
    vectorizer, tfidf_matrix = create_tfidf_vectorizer(movies)
    results = search(movie_name, vectorizer, tfidf_matrix, movies)
    movie_id = results.iloc[0]["movieId"]
    recommendations = find_similar_movies(movie_id, movies, ratings)
    print(recommendations.to_json(orient='records'))  # Print as JSON
