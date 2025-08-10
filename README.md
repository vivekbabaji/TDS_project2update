# Read this file everything will happen on its own.

## 🚀 Features
- Automatically installs dependencies from `requirements.txt`
- Installs ngrok if not already installed
- Starts `uvicorn` server
- Exposes your local server publicly via ngrok
- Clean shutdown with **Ctrl+C**
---

## 📦 Prerequisites
Make sure you have:
- **Python 3.8+** installed
- **pip** installed

---


## 🔑 Getting Credentials
1. **Google API Key**  
   Get your key here:  
   [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

2. **ngrok Auth Token**  
   Register and get your token here:  
   [https://ngrok.com/](https://ngrok.com/)

   ## ONLY COPY SELECTED PART
   ![ngrog screenshot](ngrok_ss.png)

---

## 🛠️ Installation: Just execute this file and enter your credentials

### 1. Make the script executable
```bash
chmod +x start.sh
```

### 2. Then run the script 
```bash
./start.sh
```


---

# Lastly copy paste the public url
Also don't forgot to add "/api" after the url.

- ### public link

eg: https://dd0b98d2abc3.ngrok-free.app
![public link](final_public_link.png)

- ### ADd "/api"

## Final link: public link + "/api"

eg:  https://dd0b98d2abc3.ngrok-free.app/api



