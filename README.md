# Read this file everything will happen on its own.

## 🚀 Features
- Automatically installs dependencies from `requirements.txt`
- Installs ngrok if not already installed
- Starts `uvicorn` server
- Exposes your local server publicly via ngrok
- Clean shutdown with **Ctrl+C**
- Remembers existing environment variables unless you choose to change them
---

## 📦 Prerequisites
Make sure you have:
- **Python 3.8+** installed
- **pip** installed
- Your FastAPI app code ready (`main.py` or `app.py`)

---


## 🔑 Getting Credentials
1. **Google API Key**  
   Get your key here:  
   [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

2. **ngrok Auth Token**  
   Register and get your token here:  
   [https://ngrok.com/](https://ngrok.com/)

---

## 🛠️ Installation: Just execute this file and enter your credentials

### 1. Make the script executable
```bash
chmod +x start_server.sh
```

### 2. Then run the script 
```bash
./start_server.sh
```


---

# Lastly copy paste the public url


