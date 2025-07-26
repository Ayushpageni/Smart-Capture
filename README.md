
# 🧠 Smart‑Capture by Ayush Pageni

Smart‑Capture is a cross‑platform Python desktop application that lets you **preview**, **capture**, and **save images** from:

- 🖥️ USB webcams (built-in or external, including Android devices via USB)
- 🌐 IP cameras (e.g. IP Webcam app on Android)
- 🪟 Screen or window capture (ideal for demos, emulator streaming, etc.)

---

## ✨ Features

- Live video preview from USB, IP, or screen sources  
- Auto-detection of available USB camera devices  
- Ability to input and connect to MJPEG/H.264 IP camera URLs  
- Capture frames from any selected desktop window or full screen  
- Save captured frames as `.jpg` or `.png` with optional filename  
- Flash animation effect on capture  
- Browse and set a custom save folder via GUI  
- Clean, modular, and well-documented Python codebase

---

## 📦 Installation

> Requires **Python 3.8+**

1. **Clone the repository**

   ```bash
   git clone https://github.com/Ayushpageni/Smart-Capture.git
   cd Smart-Capture
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **On Linux systems**, you may need:

   ```bash
   sudo apt update
   sudo apt install python3‑tk
   ```

---

## 🧪 How to Run

```bash
python app.py
```

This opens the GUI with options to:

- Select **Camera Source** (USB / IP / Screen)
- Click **Connect** to start live preview
- Click **Capture** to freeze the current frame
- Enter a filename (optional), then click **Save** to export the image

Captured files go to `Captured_Images/` by default (changeable in-app).

---

## ⚙️ How It Works

1. **Choose a Source**  
   - **USB Camera**: pick from detected devices  
   - **IP Camera**: enter stream URL (e.g., `http://192.168.1.100:8080/video`)  
   - **Screen Capture**: select window or use full screen  

2. **Click “Connect”** to start streaming (runs in a background thread)

3. **Click “Capture”** to freeze the frame (with a brief flash effect)

4. **Click “Save”** to write the image to disk using your filename or timestamp

---

## 📁 Output Directory

By default, images are saved in:

```
Captured_Images/
```

You can specify a different folder using the **Browse Save Location** button within the app.

---

## 💻 Platform Support

| Platform | USB Camera | IP Camera | Screen Capture |
|----------|------------|-----------|----------------|
| Windows  | ✅         | ✅        | ✅ via `pygetwindow`, `pyautogui` |
| macOS    | ✅         | ✅        | ✅ via Quartz/pyobjc |
| Linux    | ✅         | ✅        | ✅ Full-screen only (window capture is limited) |

---

## 🔌 Optional Screen Capture Dependencies

- **Windows**:  
  ```bash
  pip install pygetwindow pyautogui
  ```

- **macOS**:  
  ```bash
  pip install pyobjc-framework-Quartz
  ```

These modules enable window-level capture. Without them, the app falls back to full-screen capture.

---

## 🙋 FAQ

**Q: Can I capture from my Android phone camera?**  
Yes — use an app like **IP Webcam** on your phone and input the live stream URL in the **IP Camera** mode (e.g., `http://192.168.x.x:8080/video`).

**Q: Why is the preview black or blank?**  
- Ensure the camera or IP stream URL is correct  
- Check your camera isn't used by another application  
- Re-launch the app or try reconnecting

**Q: Can I use the app without a webcam?**  
Absolutely. You can use **IP Camera** mode or **Screen Capture** mode independently.

---

## 📜 License

This project is licensed under the **MIT License** — free for personal or commercial use.

---

## 👤 Author & Contact

**Ayush Pageni**  
GitHub: [@Ayushpageni](https://github.com/Ayushpageni)  
Feel free to open issues, submit feature requests, or reach out!
