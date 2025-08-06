import requests

API_URL = "https://e583acbf92df.ngrok-free.app/query"

test_input = {
    "query": "What are the main reasons for drug recalls?"
}

response = requests.post(API_URL, json=test_input)

print("Model Response:\n", response.json()["response"])
