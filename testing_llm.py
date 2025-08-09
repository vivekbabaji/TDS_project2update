import requests

url = "http://127.0.0.1:8000/api"
files = {
    "questions.txt": open("questions/network/questions.txt", "rb"),
    "edges.csv": open("questions/network/edges.csv", "rb"),
}

response = requests.post(url, files=files)
print(response.json())