/**
 * AI Code Explainer - Frontend Logic (script.js)
 * Step 1: Frontend Prototype with Predefined Python Binary Search Demonstration
 * 
 * Features:
 * - Line numbers and stats synchronization
 * - Tab key indentation handling
 * - Sample code insertion for all supported languages
 * - Predefined educational explanation for Python Binary Search sample:
 *   * Simple English explanation with zero-based indexing breakdown
 *   * Line-by-line detailed walkthrough
 *   * Example output: "Element found at index: 3"
 *   * Debugging tips (prerequisite sorted list, O(log n) complexity, // vs /)
 * - Custom / modified code detection with transparent demo notice
 * - Clipboard copy functionality
 */

// --- Sample Code Dictionary (Beginner-friendly examples for each language) ---
const SAMPLE_CODES = {
  python: `# Python Example: Binary Search Algorithm
def binary_search(arr, target):
    """Searches for target in a sorted list and returns its index."""
    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        # Check if target is present at the middle
        if arr[mid] == target:
            return mid
        # If target is greater, ignore left half
        elif arr[mid] < target:
            left = mid + 1
        # If target is smaller, ignore right half
        else:
            right = mid - 1

    return -1

# Sorted list of numbers (Binary search requires a sorted list)
numbers = [10, 20, 30, 40, 50, 60, 70]
target_value = 40

# Execute search
result = binary_search(numbers, target_value)

if result != -1:
    print(f"Element found at index: {result}")
else:
    print("Element not found in list")
`,

  javascript: `// JavaScript Example: Reverse a String
function reverseString(str) {
    // Split into characters, reverse array, and join back
    let reversed = "";
    for (let i = str.length - 1; i >= 0; i--) {
        reversed += str[i];
    }
    return reversed;
}

const message = "Hello World";
console.log("Original:", message);
console.log("Reversed:", reverseString(message));
`,

  java: `// Java Example: Check if a number is prime
public class PrimeCheck {
    public static boolean isPrime(int n) {
        if (n <= 1) return false;
        for (int i = 2; i * i <= n; i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        int testNum = 29;
        System.out.println(testNum + " is prime? " + isPrime(testNum));
    }
}
`,

  c: `// C Example: Find the Largest Element in an Array
#include <stdio.h>

int main() {
    int numbers[] = {12, 45, 78, 23, 90, 6};
    int size = sizeof(numbers) / sizeof(numbers[0]);
    int max = numbers[0];

    for (int i = 1; i < size; i++) {
        if (numbers[i] > max) {
            max = numbers[i];
        }
    }

    printf("Largest element in array is: %d\\n", max);
    return 0;
}
`,

  cpp: `// C++ Example: Basic Vector and Range Loop
#include <iostream>
#include <vector>

int main() {
    std::vector<std::string> fruits = {"Apple", "Banana", "Cherry", "Mango"};

    std::cout << "Fruit Inventory:" << std::endl;
    for (const auto& fruit : fruits) {
        std::cout << "- " << fruit << std::endl;
    }

    return 0;
}
`
};

// --- DOM Elements ---
const codeInput = document.getElementById("codeInput");
const lineNumbers = document.getElementById("lineNumbers");
const lineCountSpan = document.getElementById("lineCount");
const charCountSpan = document.getElementById("charCount");
const languageSelect = document.getElementById("languageSelect");
const sampleCodeBtn = document.getElementById("sampleCodeBtn");
const clearCodeBtn = document.getElementById("clearCodeBtn");
const explainBtn = document.getElementById("explainBtn");
const alertBanner = document.getElementById("alertBanner");
const alertMessage = document.getElementById("alertMessage");
const closeAlertBtn = document.getElementById("closeAlertBtn");

const initialState = document.getElementById("initialState");
const loadingState = document.getElementById("loadingState");
const resultsState = document.getElementById("resultsState");
const loadingStep = document.getElementById("loadingStep");

const demoBanner = document.getElementById("demoBanner");
const demoBadge = document.getElementById("demoBadge");
const demoBannerText = document.getElementById("demoBannerText");
const resultLanguageTag = document.getElementById("resultLanguageTag");

const simpleExplanation = document.getElementById("simpleExplanation");
const lineExplanation = document.getElementById("lineExplanation");
const exampleOutput = document.getElementById("exampleOutput");
const debugSuggestions = document.getElementById("debugSuggestions");
const copyExplanationBtn = document.getElementById("copyExplanationBtn");
const copyBtnText = document.getElementById("copyBtnText");

// --- Backend API Configuration ---
const BACKEND_API_URL = "http://127.0.0.1:8000";
const badgeDot = document.getElementById("badgeDot");
const badgeText = document.getElementById("badgeText");

/**
 * Checks backend health and updates the header badge status
 */
async function checkBackendHealth() {
  try {
    const res = await fetch(`${BACKEND_API_URL}/api/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.ai_connected) {
        if (badgeText) badgeText.textContent = "AI Connected (Step 2B)";
        if (badgeDot) {
          badgeDot.style.backgroundColor = "var(--color-success)";
          badgeDot.style.boxShadow = "0 0 8px var(--color-success)";
        }
      } else {
        if (badgeText) badgeText.textContent = "Backend Connected (Step 2B)";
        if (badgeDot) {
          badgeDot.style.backgroundColor = "var(--color-success)";
          badgeDot.style.boxShadow = "0 0 8px var(--color-success)";
        }
      }
      return true;
    }
  } catch (err) {
    // Backend offline / not running
  }
  if (badgeText) badgeText.textContent = "Backend Offline";
  if (badgeDot) {
    badgeDot.style.backgroundColor = "var(--color-warning)";
    badgeDot.style.boxShadow = "0 0 8px var(--color-warning)";
  }
  return false;
}

// --- Helper Functions ---

/**
 * Updates the line numbers gutter and character/line counter stats
 */
function updateEditorStats() {
  const code = codeInput.value;
  const lines = code.split("\n");
  const count = lines.length;

  // Generate numbered list string (1\n2\n3...)
  let numbersHtml = "";
  for (let i = 1; i <= count; i++) {
    numbersHtml += i + (i < count ? "\n" : "");
  }
  lineNumbers.textContent = numbersHtml;

  // Update status footer
  lineCountSpan.textContent = `Lines: ${count}`;
  charCountSpan.textContent = `Chars: ${code.length}`;
}

/**
 * Sync scrolling between code textarea and line numbers gutter
 */
function syncScroll() {
  lineNumbers.scrollTop = codeInput.scrollTop;
}

/**
 * Show a banner alert with a custom message
 */
function showAlert(message) {
  alertMessage.textContent = message;
  alertBanner.style.display = "flex";
  setTimeout(() => {
    hideAlert();
  }, 4000);
}

/**
 * Hide the banner alert
 */
function hideAlert() {
  alertBanner.style.display = "none";
}

/**
 * Insert sample code into the editor based on current language
 */
function insertSampleCode() {
  const currentLang = (languageSelect.value || "python").toLowerCase().trim();
  const sample = SAMPLE_CODES[currentLang] || SAMPLE_CODES.python;
  
  codeInput.value = sample;
  updateEditorStats();
  hideAlert();
  codeInput.focus();
}

/**
 * Clear the code editor
 */
function clearCodeEditor() {
  codeInput.value = "";
  updateEditorStats();
  hideAlert();
  codeInput.focus();
}

/**
 * Handle Tab key press to insert 4 spaces instead of navigating away
 */
function handleTabKey(e) {
  if (e.key === "Tab") {
    e.preventDefault();
    const start = codeInput.selectionStart;
    const end = codeInput.selectionEnd;

    // Insert 4 spaces
    codeInput.value = codeInput.value.substring(0, start) + "    " + codeInput.value.substring(end);
    codeInput.selectionStart = codeInput.selectionEnd = start + 4;
    updateEditorStats();
  }
}

/**
 * Normalizes Python code for robust structural comparison:
 * - Normalizes CRLF (\r\n) and LF (\n) newlines
 * - Strips single-line comments (# ...)
 * - Strips triple-quoted docstrings ("""...""" or '''...''')
 * - Normalizes quotes (' and ` to ")
 * - Removes all whitespace (spaces, tabs, newlines)
 */
function normalizePythonCode(str) {
  if (!str) return "";
  return str
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/#.*$/gm, "")
    .replace(/("""[\s\S]*?"""|'''[\s\S]*?''')/g, "")
    .replace(/['`]/g, '"')
    .replace(/\s+/g, "")
    .trim();
}

/**
 * Robustly checks if the current code represents the built-in Python Binary Search sample.
 * Handles harmless whitespace differences (tabs vs spaces, extra newlines, Windows CRLF, quote styles).
 * If the user edits the target, array numbers, logic, or types different code, this returns false.
 */
function isPythonBinarySearchSample(code, language) {
  if (!code) return false;
  const lang = (language || "").toLowerCase().trim();
  if (lang !== "python") return false;

  const normalizedInput = normalizePythonCode(code);
  const normalizedSample = normalizePythonCode(SAMPLE_CODES.python);

  // Exact structural match after removing comments, docstrings, quotes, and whitespace
  if (normalizedInput === normalizedSample) {
    return true;
  }

  // Verification of the core statements and variables of this specific binary search sample
  const requiredTokens = [
    "defbinary_search(arr,target):",
    "left=0",
    "right=len(arr)-1",
    "whileleft<=right:",
    "mid=(left+right)//2",
    "ifarr[mid]==target:",
    "returnmid",
    "elifarr[mid]<target:",
    "left=mid+1",
    "else:",
    "right=mid-1",
    "return-1",
    "numbers=[10,20,30,40,50,60,70]",
    "target_value=40",
    "result=binary_search(numbers,target_value)"
  ];

  return requiredTokens.every(token => normalizedInput.includes(token));
}

/**
 * Render Meaningful Predefined Explanation for the Python Binary Search sample
 */
function renderBinarySearchExplanation(isBackendOnline = false) {
  resultLanguageTag.textContent = "Python";

  // Configure Banner for Predefined Binary Search Demo
  if (demoBanner) demoBanner.className = "demo-banner";
  if (demoBadge) {
    demoBadge.textContent = isBackendOnline
      ? "Step 2A: Backend Verified (HTTP 200 OK)"
      : "Frontend Demo Notice";
  }
  if (demoBannerText) {
    demoBannerText.innerHTML = isBackendOnline
      ? `FastAPI backend at <code>http://127.0.0.1:8000/api/explain</code> accepted and validated your code (HTTP 200). Displaying the pedagogical explanation for the built-in <strong>Python Binary Search</strong> sample. <strong>No live AI model is connected yet</strong> (Step 2A scaffold). Live AI model generation will be connected in Step 2B!`
      : `This is a <strong>Step 1 frontend preview</strong> showcasing a predefined, educational explanation for the built-in <strong>Python Binary Search</strong> sample. No live AI model is connected yet. In <strong>Step 2</strong>, we will connect an AI backend API to dynamically generate explanations for any code you enter!`;
  }

  // 1. Simple Code Explanation
  simpleExplanation.innerHTML = `
    <p>
      This program implements the <strong>Binary Search algorithm</strong>, a highly efficient search method used to find the position of a specific number (<code>target_value = 40</code>) inside a <strong>sorted list</strong> of numbers.
    </p>
    <p style="margin-top: 0.65rem;">
      <strong>How Binary Search Works:</strong> Rather than checking every number one by one from left to right (which is slow for large lists), Binary Search repeatedly cuts the search space in half. It calculates the middle item:
    </p>
    <ul style="margin-top: 0.4rem; padding-left: 1.4rem; line-height: 1.6;">
      <li>If the middle item equals the target, the search is finished!</li>
      <li>If the target is larger, it throws away the left half and searches the right half.</li>
      <li>If the target is smaller, it throws away the right half and searches the left half.</li>
    </ul>

    <div style="margin-top: 1rem; padding: 0.85rem 1rem; background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 8px;">
      <strong style="color: #c7d2fe;">🔢 Core Beginner Concept — Zero-Based Indexing in Python:</strong>
      <p style="margin-top: 0.35rem; font-size: 0.86rem; color: #e2e8f0;">
        In Python, list indexing starts at <strong>0</strong>, not 1! That means the first item is at index <code>0</code>, the second item is at index <code>1</code>, and the <strong>fourth item (40)</strong> is located at <strong>index 3</strong>.
      </p>

      <div class="index-visualizer-container">
        <div class="index-visualizer-title">
          <span>List Visualization:</span>
          <code style="color: #a5b4fc;">numbers = [10, 20, 30, 40, 50, 60, 70]</code>
        </div>
        <div class="index-visualizer">
          <div class="index-cell">
            <span class="index-num">idx 0</span>
            <span class="index-val">10</span>
          </div>
          <div class="index-cell">
            <span class="index-num">idx 1</span>
            <span class="index-val">20</span>
          </div>
          <div class="index-cell">
            <span class="index-num">idx 2</span>
            <span class="index-val">30</span>
          </div>
          <div class="index-cell target-found">
            <span class="index-num">idx 3</span>
            <span class="index-val">40</span>
            <span class="index-tag">Target!</span>
          </div>
          <div class="index-cell">
            <span class="index-num">idx 4</span>
            <span class="index-val">50</span>
          </div>
          <div class="index-cell">
            <span class="index-num">idx 5</span>
            <span class="index-val">60</span>
          </div>
          <div class="index-cell">
            <span class="index-num">idx 6</span>
            <span class="index-val">70</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // 2. Line-by-Line Breakdown
  lineExplanation.innerHTML = `
    <div class="line-item">
      <span class="line-tag">Line 2</span>
      <div class="line-desc">
        <code class="code-snippet">def binary_search(arr, target):</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Defines a reusable function named <code>binary_search</code> with two parameters: <code>arr</code> (the sorted list) and <code>target</code> (the value we want to find).
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 4–5</span>
      <div class="line-desc">
        <code class="code-snippet">left = 0</code> &nbsp; <code class="code-snippet">right = len(arr) - 1</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Initializes two boundary pointers. <code>left</code> points to the start (index 0). <code>right</code> points to the last index (<code>len(arr) - 1</code>, which is 6 in our 7-item list).
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Line 7</span>
      <div class="line-desc">
        <code class="code-snippet">while left &lt;= right:</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          A loop that continues running as long as the search boundary is valid. If <code>left</code> exceeds <code>right</code>, it means the target does not exist in the list.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Line 8</span>
      <div class="line-desc">
        <code class="code-snippet">mid = (left + right) // 2</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Calculates the midpoint index. The integer division operator (<code>//</code>) rounds down to ensure <code>mid</code> is always a valid integer index.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 11–12</span>
      <div class="line-desc">
        <code class="code-snippet">if arr[mid] == target: return mid</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Checks if the middle element matches our target. If it matches, the function immediately returns <code>mid</code> (the index where it was found).
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 14–15</span>
      <div class="line-desc">
        <code class="code-snippet">elif arr[mid] &lt; target: left = mid + 1</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          If the middle element is smaller than the target, the target must be in the right half. We update <code>left = mid + 1</code> to ignore the left half.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 17–18</span>
      <div class="line-desc">
        <code class="code-snippet">else: right = mid - 1</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          If the middle element is larger than the target, the target must be in the left half. We update <code>right = mid - 1</code> to ignore the right half.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Line 20</span>
      <div class="line-desc">
        <code class="code-snippet">return -1</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          If the loop finishes without finding the target, the function returns <code>-1</code>, signaling that the target is absent from the list.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 23–24</span>
      <div class="line-desc">
        <code class="code-snippet">numbers = [10, 20, 30, 40, 50, 60, 70]</code> &nbsp; <code class="code-snippet">target_value = 40</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Defines a sorted test list and assigns the value we wish to search for (<code>40</code>).
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Line 27</span>
      <div class="line-desc">
        <code class="code-snippet">result = binary_search(numbers, target_value)</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Executes the search function and stores the returned index value (<code>3</code>) into the variable <code>result</code>.
        </p>
      </div>
    </div>

    <div class="line-item">
      <span class="line-tag">Lines 29–32</span>
      <div class="line-desc">
        <code class="code-snippet">if result != -1: print(...) else: ...</code>
        <p style="margin-top: 0.3rem; font-size: 0.85rem; color: #cbd5e1;">
          Verifies whether the target was found. Since <code>result = 3</code>, it prints: <code>Element found at index: 3</code>.
        </p>
      </div>
    </div>
  `;

  // 3. Example Output
  exampleOutput.textContent = `$ python binary_search.py\n\nElement found at index: 3`;

  // 4. Debugging & Error Suggestions
  debugSuggestions.innerHTML = `
    <div class="debug-item">
      <span class="debug-icon">⚠️</span>
      <div>
        <strong style="color: #fde68a;">Strict Prerequisite: The List Must Be Sorted</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.2rem;">
          Binary search relies strictly on sorted order to eliminate half of the candidates at each step. If you pass an unsorted list (e.g. <code>[40, 10, 70, 20]</code>), the algorithm will make incorrect decisions and fail. Always ensure your list is sorted in ascending order first (e.g., using <code>numbers.sort()</code>).
        </p>
      </div>
    </div>

    <div class="debug-item">
      <span class="debug-icon">⚡</span>
      <div>
        <strong style="color: #6ee7b7;">Time Complexity: O(log n)</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.2rem;">
          Binary search operates in logarithmic time — <strong>O(log n)</strong>. Because it divides the list in half each iteration, searching through 1,000 items takes at most ~10 comparisons, whereas a linear search (O(n)) would require up to 1,000 comparisons.
        </p>
      </div>
    </div>

    <div class="debug-item">
      <span class="debug-icon">0️⃣</span>
      <div>
        <strong style="color: #93c5fd;">Zero-Based Indexing Pitfall</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.2rem;">
          A common beginner confusion is thinking index <code>3</code> means the 3rd item. In Python, counting starts at <code>0</code>: <code>numbers[0]</code> is the 1st item, <code>numbers[1]</code> is the 2nd, <code>numbers[2]</code> is the 3rd, and <code>numbers[3]</code> is the <strong>4th item</strong>.
        </p>
      </div>
    </div>

    <div class="debug-item">
      <span class="debug-icon">➗</span>
      <div>
        <strong style="color: #fda4af;">Integer Division (// vs /)</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.2rem;">
          Always use <code>//</code> (floor division) when calculating <code>mid</code>. Using single slash <code>/</code> returns a floating-point number (e.g., <code>3.5</code>), triggering a <code>TypeError: list indices must be integers or slices, not float</code>.
        </p>
      </div>
    </div>

    <div class="debug-item">
      <span class="debug-icon">🔁</span>
      <div>
        <strong style="color: #e2e8f0;">Loop Condition Off-By-One (<= vs <)</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.2rem;">
          Ensure the while-loop uses <code>while left &lt;= right:</code>. Using <code>&lt;</code> instead of <code>&lt;=</code> causes the algorithm to miss evaluating the final remaining candidate when <code>left == right</code>.
        </p>
      </div>
    </div>
  `;
}

/**
 * Render Demo Notice for Custom or Modified Code
 * Explicitly informs user that Step 1 is frontend only and does not claim to analyze custom code.
 */
function renderCustomCodeNotice(code, language, isBackendOnline = false, backendData = null) {
  const lines = code.trim().split("\n");
  const langUpper = language.charAt(0).toUpperCase() + language.slice(1);
  resultLanguageTag.textContent = langUpper;

  // Case 1: Backend is online and returned a structured response
  if (backendData) {
    const isAI = backendData.is_ai_connected === true;

    if (demoBanner) demoBanner.className = isAI ? "demo-banner" : "demo-banner custom-code";
    if (demoBadge) {
      demoBadge.textContent = isAI
        ? "✨ Step 2B: AI Explanation Generated"
        : "Step 2B: Backend Response (Placeholder)";
    }
    if (demoBannerText) {
      demoBannerText.innerHTML = isAI
        ? `
            This explanation was <strong>generated live by the Google Gemini AI</strong> for your custom
            <strong>${langUpper}</strong> code
            (<strong>${backendData.code_length}</strong> characters,
            <strong>${backendData.line_count}</strong> lines).
            Model: <code>${backendData.message || "Gemini"}</code>.
          `
        : `
            FastAPI backend at <code>http://127.0.0.1:8000/api/explain</code> accepted your custom
            <strong>${langUpper}</strong> code
            (<strong>${backendData.code_length}</strong> characters,
            <strong>${backendData.line_count}</strong> lines).
            The backend returned a <strong>placeholder response</strong> — no live AI model was queried
            (AI_ENABLED is false or no valid API key is configured).
          `;
    }

    // 1. Simple Explanation from Backend
    simpleExplanation.innerHTML = `
      <p>${escapeHtml(backendData.simple_explanation)}</p>
      <p style="margin-top: 0.65rem; font-size: 0.85rem; color: #60a5fa;">
        💡 <em>Tip: To see the full interactive demonstration of our structured explanation cards right now, click <strong>"Insert Sample Code"</strong> (with Python selected) and click <strong>"Explain Code"</strong>!</em>
      </p>
    `;

    // 2. Line-by-Line Breakdown from Backend
    let lineItemsHtml = "";
    if (backendData.line_by_line && backendData.line_by_line.length > 0) {
      backendData.line_by_line.forEach(item => {
        lineItemsHtml += `
          <div class="line-item">
            <span class="line-tag">Line ${item.line_number}</span>
            <div class="line-desc">
              <code class="code-snippet">${escapeHtml(item.code_snippet)}</code>
              <p style="margin-top: 0.25rem; font-size: 0.82rem; color: #94a3b8;">
                ${escapeHtml(item.explanation)}
              </p>
            </div>
          </div>
        `;
      });
    }
    if (backendData.line_count > 5) {
      lineItemsHtml += `
        <div class="line-item" style="color: #64748b; font-size: 0.82rem; padding-top: 0.5rem;">
          + ${backendData.line_count - 5} more lines will be annotated step-by-step by AI once connected in Step 2B.
        </div>
      `;
    }
    lineExplanation.innerHTML = lineItemsHtml;

    // 3. Example Output from Backend
    exampleOutput.textContent = backendData.example_output;

    // 4. Debugging Suggestions from Backend
    let debugHtml = "";
    if (backendData.debugging_suggestions && backendData.debugging_suggestions.length > 0) {
      backendData.debugging_suggestions.forEach(tip => {
        debugHtml += `
          <div class="debug-item">
            <span class="debug-icon">⚡</span>
            <div>
              <p style="font-size: 0.84rem; color: #cbd5e1;">${escapeHtml(tip)}</p>
            </div>
          </div>
        `;
      });
    }
    debugSuggestions.innerHTML = debugHtml;
    return;
  }

  // Case 2: Fallback when backend is offline
  if (demoBanner) demoBanner.className = "demo-banner custom-code";
  if (demoBadge) demoBadge.textContent = "Frontend Demo Notice: Custom / Modified Code";
  if (demoBannerText) {
    demoBannerText.innerHTML = `
      You entered or edited custom code. <strong>No real AI is connected yet</strong> (Step 1 is frontend only). 
      To maintain honesty, we do not show a false AI analysis for custom code. In <strong>Step 2</strong>, we will connect an AI backend API (such as Google Gemini API) to generate dynamic, live explanations for any custom code you paste!
    `;
  }

  // 1. Simple Explanation
  simpleExplanation.innerHTML = `
    <p>You submitted a custom <strong>${langUpper}</strong> snippet containing <strong>${lines.length} lines</strong> of code.</p>
    <p style="margin-top: 0.5rem; color: #94a3b8;">
      In <strong>Step 2</strong>, when our AI backend is integrated, our AI model will dynamically analyze this specific logic and generate a tailored summary in plain English.
    </p>
    <p style="margin-top: 0.65rem; font-size: 0.85rem; color: #60a5fa;">
      💡 <em>Tip: To see the full interactive demonstration of our structured explanation cards right now, click <strong>"Insert Sample Code"</strong> (with Python selected) and click <strong>"Explain Code"</strong>!</em>
    </p>
  `;

  // 2. Line-by-Line Breakdown Preview
  const previewLines = lines.slice(0, 4);
  let lineItemsHtml = "";
  
  previewLines.forEach((line, index) => {
    const displayLine = line.trim() || "// (empty line)";
    lineItemsHtml += `
      <div class="line-item">
        <span class="line-tag">Line ${index + 1}</span>
        <div class="line-desc">
          <code class="code-snippet">${escapeHtml(displayLine)}</code>
          <p style="margin-top: 0.25rem; font-size: 0.82rem; color: #94a3b8;">
            AI line analysis will be generated dynamically in Step 2.
          </p>
        </div>
      </div>
    `;
  });

  if (lines.length > 4) {
    lineItemsHtml += `
      <div class="line-item" style="color: #64748b; font-size: 0.82rem; padding-top: 0.5rem;">
        + ${lines.length - 4} more lines will be annotated step-by-step by AI once connected.
      </div>
    `;
  }

  lineExplanation.innerHTML = lineItemsHtml;

  // 3. Example Output Preview
  exampleOutput.textContent = `$ [Step 2 AI Simulation]\n\nExecution preview will be dynamically simulated by the AI backend in Step 2.`;

  // 4. Debugging & Error Suggestions
  debugSuggestions.innerHTML = `
    <div class="debug-item">
      <span class="debug-icon">⚡</span>
      <div>
        <strong>AI Code Analysis & Validation:</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.15rem;">
          In Step 2, the AI model will evaluate your code for potential edge-case bugs, type errors, and performance bottlenecks.
        </p>
      </div>
    </div>
    <div class="debug-item">
      <span class="debug-icon">💡</span>
      <div>
        <strong>Optimization Advice:</strong>
        <p style="font-size: 0.84rem; color: #94a3b8; margin-top: 0.15rem;">
          The AI will provide idiomatic refactoring tips and computational complexity analysis (Big-O) for your custom algorithm.
        </p>
      </div>
    </div>
  `;
}

/**
 * Simple HTML escape utility to avoid XSS in user code previews
 */
function escapeHtml(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Handle Explain Code Click
 */
async function handleExplainClick() {
  const code = codeInput.value;
  const trimmedCode = code.trim();
  const language = (languageSelect.value || "python").toLowerCase().trim();

  // Requirement: Helpful message when code editor is empty
  if (!trimmedCode) {
    showAlert("Please enter some code or click 'Insert Sample Code' first!");
    codeInput.focus();
    return;
  }

  hideAlert();

  // Switch to Loading State
  initialState.style.display = "none";
  resultsState.style.display = "none";
  loadingState.style.display = "flex";
  loadingStep.textContent = "Connecting to FastAPI backend at http://127.0.0.1:8000...";

  let backendData = null;
  let backendError = null;
  let isBackendOnline = false;

  // Real fetch call to FastAPI backend /api/explain
  try {
    const response = await fetch(`${BACKEND_API_URL}/api/explain`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        code: code,
        language: language
      })
    });

    if (response.ok) {
      backendData = await response.json();
      isBackendOnline = true;
      // Update header badge based on actual AI connection status from backend
      const isAI = backendData.is_ai_connected === true;
      if (badgeText) badgeText.textContent = isAI ? "✨ AI Connected (Step 2B)" : "Backend Connected (Step 2B)";
      if (badgeDot) {
        badgeDot.style.backgroundColor = "var(--color-success)";
        badgeDot.style.boxShadow = "0 0 8px var(--color-success)";
      }
    } else {
      isBackendOnline = true;
      const errorJson = await response.json().catch(() => null);
      backendError = (errorJson && errorJson.detail) ? errorJson.detail : `Server error (${response.status})`;
    }
  } catch (err) {
    // Backend offline / network failure: fallback smoothly to client demo
    isBackendOnline = false;
    if (badgeText) badgeText.textContent = "Step 1: Frontend UI Demo";
    if (badgeDot) {
      badgeDot.style.backgroundColor = "var(--color-warning)";
      badgeDot.style.boxShadow = "0 0 8px var(--color-warning)";
    }
  }

  // Handle server-side validation error (e.g. code too large or empty)
  if (backendError) {
    loadingState.style.display = "none";
    showAlert(backendError);
    initialState.style.display = "flex";
    return;
  }

  loadingStep.textContent = isBackendOnline
    ? "FastAPI response received. Formatting presentation cards..."
    : "Formatting code and preparing presentation cards...";

  // Smooth loading indicator
  setTimeout(() => {
    loadingState.style.display = "none";
    resultsState.style.display = "flex";

    // Check whether user is running the built-in Python Binary Search sample or custom code
    if (isPythonBinarySearchSample(code, language)) {
      renderBinarySearchExplanation(isBackendOnline);
    } else {
      renderCustomCodeNotice(code, language, isBackendOnline, backendData);
    }
  }, 400);
}

/**
 * Copy displayed explanation to clipboard
 */
function copyExplanationToClipboard() {
  // If results aren't displayed yet, notify user
  if (resultsState.style.display === "none") {
    showAlert("Please generate an explanation first by clicking 'Explain Code'!");
    return;
  }

  // Build clean text representation of all 4 output sections
  const lang = resultLanguageTag.textContent;
  const simpleText = simpleExplanation.innerText;
  const linesText = lineExplanation.innerText;
  const outputText = exampleOutput.innerText;
  const debugText = debugSuggestions.innerText;

  const fullText = `=== AI Code Explainer Analysis (${lang}) ===\n\n` +
    `1. SIMPLE EXPLANATION:\n${simpleText}\n\n` +
    `2. LINE-BY-LINE BREAKDOWN:\n${linesText}\n\n` +
    `3. EXAMPLE OUTPUT:\n${outputText}\n\n` +
    `4. DEBUGGING & SUGGESTIONS:\n${debugText}\n`;

  navigator.clipboard.writeText(fullText).then(() => {
    // Provide visual feedback
    const originalText = copyBtnText.textContent;
    copyBtnText.textContent = "Copied!";
    copyExplanationBtn.style.backgroundColor = "rgba(16, 185, 129, 0.25)";
    copyExplanationBtn.style.borderColor = "rgba(16, 185, 129, 0.5)";

    setTimeout(() => {
      copyBtnText.textContent = originalText;
      copyExplanationBtn.style.backgroundColor = "";
      copyExplanationBtn.style.borderColor = "";
    }, 2000);
  }).catch(err => {
    console.error("Clipboard copy failed:", err);
    showAlert("Failed to copy to clipboard. Please copy manually.");
  });
}

// --- Event Listeners ---

// Input & Scroll sync
codeInput.addEventListener("input", () => {
  updateEditorStats();

  // If results are already showing, check if code was modified away from sample
  if (resultsState.style.display !== "none") {
    const isSample = isPythonBinarySearchSample(codeInput.value, languageSelect.value);
    if (!isSample && demoBanner && demoBadge && demoBannerText) {
      demoBanner.className = "demo-banner custom-code";
      demoBadge.textContent = "Frontend Demo Notice: Code Modified";
      demoBannerText.innerHTML = `
        The code in the editor was modified. Click <strong>"Explain Code"</strong> to update the cards for your custom code.
      `;
    }
  }
});
codeInput.addEventListener("scroll", syncScroll);
codeInput.addEventListener("keydown", handleTabKey);

// Buttons
explainBtn.addEventListener("click", handleExplainClick);
sampleCodeBtn.addEventListener("click", insertSampleCode);
clearCodeBtn.addEventListener("click", clearCodeEditor);
closeAlertBtn.addEventListener("click", hideAlert);
copyExplanationBtn.addEventListener("click", copyExplanationToClipboard);

// When language changes, update sample code if user currently has another sample loaded
languageSelect.addEventListener("change", () => {
  const currentVal = codeInput.value.trim();
  const isHoldingSample = Object.values(SAMPLE_CODES).some(s => {
    return normalizePythonCode(s) === normalizePythonCode(currentVal);
  });
  if (isHoldingSample) {
    insertSampleCode();
  }
});

// Initial Setup
updateEditorStats();
checkBackendHealth();
