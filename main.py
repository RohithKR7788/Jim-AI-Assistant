import cv2
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import requests
import base64
import numpy as np
import time
import subprocess
import pytesseract
from PIL import Image
import os
import webbrowser
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ultralytics import YOLO

memory=[]
scene_memory = {
    "last_objects": [],
    "current_objects": []
}
# ===================== SPEAK FUNCTION (FIXED) =====================
# ===== FILE SEARCH (SMART) =====
def find_file(filename):
    search_paths = [
        "C:/Users/Lenovo/Desktop",
        "C:/Users/Lenovo/Documents",
        "C:/Users/Lenovo/Downloads"
    ]

    for path in search_paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if filename.lower() in file.lower():
                    return os.path.join(root, file)

    return None
def open_notepad_and_write(text):
    speak("Opening Notepad")

    os.system("start notepad")
    time.sleep(2)

    pyautogui.write(text, interval=0.05)

def is_object_question(text):
    keywords = ["what is", "what am i holding", "object", "identify"]
    return any(word in text.lower() for word in keywords)

def open_chatgpt():
    url = "https://chat.openai.com"
    webbrowser.open(url)
    speak("Opening ChatGPT")

def open_chatgpt_app():
    try:
        os.system("start ChatGPT")
        speak("Opening ChatGPT app")
    except:
        open_chatgpt()

def open_app(app_name):
    try:
        if app_name == "spotify":
            os.startfile(r"C:\Users\Lenovo\AppData\Roaming\Spotify\Spotify.exe")
        else:
            os.system(f"start {app_name}")

        speak(f"Opening {app_name}")
    except Exception as e:
        print(e)
        speak("I couldn't open that app")

def youtube_play(query):
    speak("Opening YouTube")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.youtube.com")

    time.sleep(3)

    # find search box
    search_box = driver.find_element(By.NAME, "search_query")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)

    # click first video
    video = driver.find_element(By.ID, "video-title")
    video.click()

def spotify_play(query):
    speak("Opening Spotify")

    open_app("spotify")
    time.sleep(5)  # wait for app to open

    # Focus search bar (CTRL + L works in Spotify)
    pyautogui.hotkey("ctrl", "l")
    time.sleep(1)

    # Type query
    pyautogui.write(query)
    time.sleep(1)

    pyautogui.press("enter")
    time.sleep(3)

    # Press TAB a few times to reach first song
    for _ in range(4):
        pyautogui.press("tab")

    pyautogui.press("enter")  # play song

def open_google_search(query):
    speak("Searching Google")
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

def press_key(key):
    pyautogui.press(key)

def type_text(text):
    pyautogui.write(text, interval=0.05)

def open_app_general(app):
    try:
        os.system(f"start {app}")
        speak(f"Opening {app}")
    except:
        speak("Couldn't open app")

def move_mouse(x, y):
    pyautogui.moveTo(x, y, duration=0.5)

def click_mouse():
    pyautogui.click()

def speak(text):
    # Remove problematic characters
    safe_text = text.replace("'", "").replace('"', "")

    command = [
        "powershell",
        "-Command",
        f"Add-Type -AssemblyName System.Speech; "
        f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$speak.Speak(\"{safe_text}\")"
    ]

    subprocess.run(command)
# ===================== MODELS =====================
wake_model = whisper.load_model("base")
main_model = whisper.load_model("base")

# ===================== CAMERA =====================
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # width
cap.set(4, 720)   # height

# ===================== WAKE WORD =====================
def listen_for_wake_word():
    fs = 16000
    seconds = 3

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()

    write("wake.wav", fs, audio)

    result = wake_model.transcribe("wake.wav")
    text = result["text"].lower()

    print("Heard:", text)

    wake_words = ["jim", "gym", "gim", "ji","g","j"]

    return any(word in text for word in wake_words)

def read_text_normal():
    try:
        img = Image.open("frame.jpg")

        text = pytesseract.image_to_string(img)
        text = text.strip()
        text = " ".join(text.split())

        print("OCR (NORMAL):", text)
        return text

    except Exception as e:
        print("OCR ERROR:", e)
        return ""
def read_text_screen():
    try:
        img = cv2.imread("frame.jpg")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=2, beta=50)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        cv2.imwrite("processed.jpg", thresh)

        text = pytesseract.image_to_string(thresh)
        text = text.strip()
        text = " ".join(text.split())

        print("OCR (SCREEN):", text)
        return text

    except Exception as e:
        print("OCR ERROR:", e)
        return ""

# load model once
yolo_model = YOLO("yolov8n.pt")
def estimate_fingers():
    results = yolo_model("frame.jpg")

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = yolo_model.names[cls_id]

            if label == "person":
                return "Hand detected, likely showing fingers (cannot count precisely)"

    return "No hand clearly detected"

def is_finger_question(text):
    keywords = ["finger", "fingers", "hand"]
    return any(word in text.lower() for word in keywords)

def detect_objects():
    results = yolo_model("frame.jpg")

    detected = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = yolo_model.names[cls_id]
            detected.append(label)

    detected = list(set(detected))

    # update memory
    scene_memory["last_objects"] = scene_memory["current_objects"]
    scene_memory["current_objects"] = detected

    if not detected:
        return "No objects detected"

    return ", ".join(detected)

def get_scene_changes():
    previous = set(scene_memory["last_objects"])
    current = set(scene_memory["current_objects"])

    appeared = current - previous
    disappeared = previous - current

    return appeared, disappeared

def is_memory_question(text):
    keywords = ["where did", "what happened", "before", "earlier", "previous"]
    return any(word in text.lower() for word in keywords)

def smart_ocr(vision_text):
    vision_text = vision_text.lower()

    use_screen = any(word in vision_text for word in ["phone", "screen", "monitor", "laptop", "display"])

    if use_screen:
        print("Using SCREEN OCR (vision-based)")
        text = read_text_screen()
    else:
        print("Using NORMAL OCR (vision-based)")
        text = read_text_normal()

    # fallback if weak
    if len(text.strip()) < 3:
        print("Weak OCR → trying alternate method")

        if use_screen:
            text = read_text_normal()
        else:
            text = read_text_screen()

    return text
# ===================== RECORD COMMAND =====================
def record_command():
    fs = 16000
    seconds = 7

    print("Recording command...")
    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()

    write("audio.wav", fs, audio)

# ===================== SPEECH TO TEXT =====================
def speech_to_text():
    print("Transcribing...")
    result = main_model.transcribe("audio.wav")
    text = result["text"]
    print("You said:", text)
    return text

def is_text_question(text):
    keywords = ["read", "text", "written", "number", "time", "date"]
    return any(word in text.lower() for word in keywords)

# ===================== IMAGE =====================
def capture_image():
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("frame.jpg", frame)
        print("Image captured")

def analyze_image():
    with open("frame.jpg", "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "moondream",
            "prompt": "Describe what you see in this image",
            "images": [image_base64],
            "stream": False
        }
    )

    return response.json()["response"]

# ===================== AI =====================
def ask_ai(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# ===================== TEST SPEECH =====================
print("Testing voice...")
speak("System ready")

# ===================== MAIN LOOP =====================
print("Say 'JIM' to activate...")

while True:
    triggered = listen_for_wake_word()

    if triggered:
        print("Wake word detected!")

        time.sleep(0.5)
        speak("Yes")
        time.sleep(1.5)

        record_command()
        text = speech_to_text()

        if not text.strip():
            speak("I didn't catch that")
            continue

        text_lower = text.lower()

        # ================= COMMAND HANDLING =================

        # ===== NOTEPAD WRITE (TOP PRIORITY) =====
        if "notepad" in text_lower and "write" in text_lower:
            content = text.split("write", 1)[1].strip()
            open_notepad_and_write(content)
            continue

        # ===== GOOGLE SEARCH =====
        if "google" in text_lower and "search" in text_lower:
            query = text_lower.split("search", 1)[1].strip()
            open_google_search(query)
            continue

        # ===== YOUTUBE =====
        if "youtube" in text_lower:
            query = text_lower.replace("open youtube and play", "").replace("youtube", "").strip()
            youtube_play(query)
            continue

        # ===== SPOTIFY =====
        if "spotify" in text_lower:
            query = text_lower.replace("open spotify and play", "").replace("spotify", "").strip()
            spotify_play(query)
            continue

        # ===== CHATGPT =====
        if "chatgpt" in text_lower:
            open_chatgpt_app()
            continue

        # ===== FILE NAME COMMAND (FIXED) =====
        if "open file named" in text_lower:
            name = text_lower.split("open file named", 1)[1].strip()

            result = find_file(name)

            if result:
                print("Found:", result)
                speak("Opening file")
                os.startfile(result)
            else:
                speak("File not found")

            continue
        # ===== FLEXIBLE FILE COMMAND =====
        if "file" in text_lower and "open" in text_lower:
            words = text_lower.replace("open", "").replace("file", "").strip()

            result = find_file(words)

            if result:
                speak("Opening file")
                os.startfile(result)
            else:
                speak("File not found")

            continue
        # ===== FILE SEARCH (FIXED) =====
        if text_lower.startswith("open"):
            name = text_lower.replace("open", "").strip()

            blocked = ["youtube", "spotify", "google", "notepad", "chatgpt"]

            if not any(x in name for x in blocked):
                result = find_file(name)

                if result:
                    print("Found:", result)
                    speak("Opening file")
                    os.startfile(result)
                else:
                    speak("File not found")

                continue

        # ===== GENERAL APP OPEN =====
        if text_lower.startswith("open"):
            app = text_lower.replace("open", "").strip()
            open_app_general(app)
            continue

        # ===== TYPE =====
        if "type" in text_lower:
            content = text.split("type", 1)[1].strip()
            type_text(content)
            continue

        # ===== PRESS KEY =====
        if "press" in text_lower:
            key = text_lower.split("press", 1)[1].strip()
            press_key(key)
            continue

        # ===== CLICK =====
        if "click" in text_lower:
            click_mouse()
            continue


        # ================= VISION + AI =================

        capture_image()
        vision_text = analyze_image()
        ocr_text = smart_ocr(vision_text)

        if is_finger_question(text):
            final_context = estimate_fingers()

        elif is_text_question(text):
            final_context = ocr_text if ocr_text else "No readable text found"

        elif is_object_question(text):
            objects = detect_objects()
            final_context = f"Detected objects: {objects}"

        elif is_memory_question(text):
            appeared, disappeared = get_scene_changes()
            final_context = f"Appeared: {list(appeared)}, Disappeared: {list(disappeared)}"

        else:
            final_context = vision_text

        print("Vision:", vision_text)
        print("OCR:", ocr_text)

        history = "\n".join(memory[-8:])

        prompt = f"""
User question: {text}

Vision description: {vision_text}
OCR text: {ocr_text}
Extra context: {final_context}

Rules:
- If object detection is available, use it
- If finger count exists, use it
- If finger count is unclear estimate based on vision 
- If text question → use OCR
- Otherwise → use vision
- Use memory for changes
- Be direct and accurate

Answer clearly.
"""

        response = ask_ai(prompt)

        print("\nAssistant:", response)

        memory.append(f"User: {text}")
        memory.append(f"Seen: {vision_text}")
        memory.append(f"Read text: {ocr_text}")
        memory.append(f"Assistant: {response}")

        if len(memory) > 10:
            memory = memory[-10:]

        time.sleep(0.5)
        short_response = response[:200]  # limit length
        speak(short_response)

# ===================== CLEANUP =====================
cap.release()
cv2.destroyAllWindows()