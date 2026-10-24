# AI Code Explainer 🚀

> **Understand code. Learn faster.**  
> A modern web application designed to help beginner engineering students understand programming code step-by-step.

---

## 📌 Project Overview
As engineering students learning computer science, reading other people's code or deciphering complex syntax can be intimidating. **AI Code Explainer** is built to bridge that gap by breaking down any code snippet into:
1. **Simple Code Explanation** (High-level English summary)
2. **Line-by-Line Breakdown** (Detailed walkthrough of key statements)
3. **Example Output** (Expected console or terminal results)
4. **Common Errors & Debugging Tips** (Edge cases, caveats, and best practices)

---

## 🎯 Step 1 — Frontend Implementation (Completed)
In **Step 1**, we built the complete frontend client user interface without external APIs, backends, or paid dependencies.

### 📁 Project Structure
```text
AI-Code-Explainer/
├── index.html       # Semantic HTML5 layout, toolbar, editor & card containers
├── style.css        # Modern dark-theme styling, glassmorphism & responsive grid
├── script.js        # Interactive behaviors, sample codes, validation & copy logic
└── README.md        # Documentation, testing steps & Step 2 roadmap
```

### ✨ Features Implemented in Step 1
- **Modern Dashboard Design**: Sleek dark IDE theme with glassmorphic cards, glowing ambient accents, and crisp typography (`Inter` and `Fira Code`).
- **Code Editor with Line Numbers**: Monospace code input area with live line numbering, character count, and line count stats.
- **Tab Key Indentation**: Pressing `Tab` inserts 4 spaces instead of jumping out of the editor.
- **Language Selector**: Dropdown supporting Python, JavaScript, Java, C, and C++.
- **Sample Code Generator**: Instant "Insert Sample Code" button that loads clean snippets, featuring a beginner-friendly **Binary Search Algorithm** for Python.
- **Clear Button**: One-click reset for the source code editor.
- **Helpful Validation Banner**: Alert banner that warns users if they click "Explain Code" without entering any code.
- **Loading State Indicator**: Realistic animated spinner demonstrating loading progress.
- **4 Predefined Output Cards for Python Binary Search**:
  - 💡 **Simple Code Explanation**: Plain English explanation of how Binary Search eliminates half the remaining items at each step, plus an interactive visual table explaining **0-based indexing** in Python.
  - 🔍 **Line-by-Line Breakdown**: Pedagogical walkthrough explaining function definitions, pointer boundaries (`left` & `right`), integer division (`//`), and conditionals.
  - 💻 **Example Output**: Displays `Element found at index: 3` with an explanation of why target `40` is at index 3.
  - ⚠️ **Debugging Tips & Caveats**: Highlights the strict requirement of a sorted list, **O(log n)** time complexity vs O(n) linear search, 0-based indexing pitfall, and `//` vs `/` integer division.
- **Transparent Step 1 Demo Notices**:
  - **Predefined Sample Notice**: Clearly marks the Binary Search explanation as a frontend preview.
  - **Custom Code Notice**: If a user enters or modifies code, a transparent banner informs them that real-time AI analysis is not yet active (Step 1 is frontend only) and will be hooked up in Step 2.
- **Copy Explanation Button**: One-click copy that formats all 4 sections into the clipboard with visual "Copied!" feedback.
- **Responsive Layout**: Adapts gracefully across desktop, tablet, and mobile screens.

---

## 💻 How to Run the Website Locally

Since Step 1 is built with pure HTML, CSS, and Vanilla JavaScript, no installation or `npm` setup is required!

### Method 1: Double-click (Quickest)
1. Open Windows File Explorer.
2. Navigate to:  
   `C:\Users\Puramjay\OneDrive\Desktop\AI Code Explainer._project\AI-Code-Explainer`
3. Double-click **`index.html`** to open it in your default web browser (Chrome, Edge, Firefox, Brave, etc.).

### Method 2: From Antigravity Terminal / PowerShell
In PowerShell, run:
```powershell
Start-Process "AI-Code-Explainer\index.html"
```

---

## 🧪 How to Test Every Feature in Step 1

Follow this checklist to verify all frontend interactions:

| Feature | How to Test | Expected Result |
| :--- | :--- | :--- |
| **1. Empty Input Alert** | Leave the code editor empty and click **"Explain Code"**. | A yellow alert appears saying *"Please enter some code or click 'Insert Sample Code' first!"*. |
| **2. Close Alert** | Click the `×` button on the alert banner. | The alert dismisses smoothly. |
| **3. Binary Search Sample** | Ensure Python is selected and click **"Insert Sample Code"**. | The Python Binary Search algorithm is inserted, line numbers update, and character count updates. |
| **4. Explain Binary Search** | Click **"Explain Code"** with the Python Binary Search sample loaded. | After a ~1s loading spinner, all 4 cards appear with: <br>• Simple explanation with **zero-based indexing visualizer**<br>• Line-by-line breakdown<br>• Example output: `Element found at index: 3`<br>• Debugging tips with **O(log n)** complexity & sorted list requirements. |
| **5. Custom Code Notice** | Change a number in the code or type custom code, then click **"Explain Code"**. | The banner updates to **"Frontend Demo Notice: Custom / Modified Code"** explaining that real AI is not connected yet, without showing false AI claims. |
| **6. Language Switch** | Change dropdown to **JavaScript** or **C++**, then click **"Insert Sample Code"**. | The editor loads the respective language snippet. |
| **7. Tab Indentation** | Click inside the code editor and press the `Tab` key. | 4 spaces are inserted at the cursor position without losing focus. |
| **8. Stats Counter** | Type new lines into the editor. | The bottom footer updates **Lines** and **Chars** in real time. |
| **9. Clear Button** | Click the **"Clear"** button in the editor toolbar. | All text is cleared, and lines reset to 1. |
| **10. Copy Explanation** | Click **"Copy Explanation"** in the top-right of the output panel. | The button turns green and shows *"Copied!"*. Paste into Notepad to verify the formatted text. |
| **11. Responsive Layout** | Resize your browser window to a narrow mobile width. | The layout shifts seamlessly from side-by-side to a vertical stack. |

---

---

## 🐍 Step 2A — Python Backend with FastAPI

In **Step 2A**, we established the Python backend service using **FastAPI** to power the future AI processing pipeline.

### 📁 Updated Project Structure
```text
AI-Code-Explainer/
├── backend/
│   ├── main.py          # FastAPI application, CORS, validation & placeholder endpoints
│   └── requirements.txt # Python dependencies (fastapi, uvicorn, pydantic)
├── index.html           # Frontend dashboard
├── style.css            # Dark IDE styling & visualizers
├── script.js            # Frontend interaction logic
└── README.md            # Project documentation & guides
```

### ⚙️ How to Set Up and Run the Backend on Windows

Follow these beginner-friendly steps in **PowerShell** or **Command Prompt**:

#### 1. Navigate to the backend folder
```powershell
cd "C:\Users\Puramjay\OneDrive\Desktop\AI Code Explainer._project\AI-Code-Explainer\backend"
```

#### 2. Create a Python Virtual Environment
A virtual environment keeps your project packages clean and isolated from your global Python installation:
```powershell
python -m venv venv
```

#### 3. Activate the Virtual Environment
```powershell
.\venv\Scripts\activate
```
*(You will see `(venv)` appear at the beginning of your terminal prompt).*

> **Tip for Windows PowerShell Execution Policy:**  
> If PowerShell shows an error like `cannot be loaded because running scripts is disabled on this system`, run this once:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`  
> and run `.\venv\Scripts\activate` again.

#### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

#### 5. Start the FastAPI Development Server
```powershell
uvicorn main:app --reload --port 8000
```
*(The `--reload` flag automatically reloads the server whenever you save changes to Python files).*

---

## 🧪 How to Test the Backend Endpoints

Once the server is running (`http://127.0.0.1:8000`), you have multiple quick ways to verify it:

### Method 1: Interactive Swagger API Documentation (Visual & Easiest)
Open your browser and navigate to:  
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**  
- You will see interactive documentation for `/api/health` and `/api/explain`.
- Click on **POST /api/health** → **Try it out** → **Execute**. You will see the response:
  ```json
  {
    "status": "ok",
    "service": "AI Code Explainer Backend",
    "version": "0.1.0",
    "step": "Step 2A - FastAPI Backend Scaffold",
    "ai_connected": false
  }
  ```

### Method 2: In Browser Address Bar (Direct GET test)
Open your browser and go to:  
👉 **[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)**  
It will immediately display the health status JSON.

### Method 3: From Windows Terminal (PowerShell)
Open a new PowerShell window and run:
```powershell
# Test Health Endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method POST

# Test Explanation Endpoint
$body = @{
    language = "python"
    code = "def add(a, b): return a + b"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/explain" -Method POST -Body $body -ContentType "application/json"
```

---

## 🔮 What We Will Add in Step 2B

Once you test and confirm Step 2A is working:
1. **Google Gemini AI SDK**: Install `google-genai` and configure API access securely via environment variables (`.env`).
2. **Pedagogical System Prompt**: Instruct Gemini to format responses into our 4 cards (Simple explanation, Line-by-line, Example output, Debugging tips).
3. **Connect Frontend to Backend**: Update [`script.js`](file:///c:/Users/Puramjay/OneDrive/Desktop/AI%20Code%20Explainer._project/AI-Code-Explainer/script.js) with `fetch('http://127.0.0.1:8000/api/explain')` to stream live AI responses to the frontend!

