# W11 RamOptimizer
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078d4.svg)](https://www.microsoft.com/windows)

**W11 RamOptimizer Core** is an advanced, production-grade system optimization and automated administration suite built for Windows 11. By merging low-level OS telemetry (`winreg`, `psutil`, `ctypes`) with advanced Generative AI capabilities via the **Google Gemini API**, this tool acts as an autonomous Systems Administrator. It detects resource leaks, categorizes system processes, eliminates bloatware via native package managers, and mitigates telemetry tracking—all through a responsive, multi-threaded GUI.

Designed with **resilience, atomicity, and high availability** at its core, this project serves as a showcase of robust Software Engineering principles applied to system-level optimization and LLM integration.

---

## 🚀 Key Features

### 🧠 Intelligent Core (AI Integration & Heuristics)
*   **Resilient Cascade LLM Routing:** Implements a fault-tolerant mechanism that automatically cycles through fallback models (`gemini-3.5-flash`, `gemini-3.1-pro-preview`, etc.) if a primary endpoint suffers a timeout or quota restriction.
*   **Batch Heuristic Classification:** Groups and pipelines active processes, scheduled tasks, and bloatware payloads to categorize them safely into `Seguro` (Safe), `Sospechoso` (Suspicious), or `Critico` (Critical) tiers.
*   **Dynamic Interactive Auditing:** Context-aware prompt injection generates real-time, expert-level system analysis reports in localized environments for any individual process or service.

### 🛡️ Core Optimization & Systems Administration
*   **Asynchronous Memory Guardian:** A background watchdog process (`psutil`) that acts on custom thread freezing/suspension algorithms (`Process.suspend()`) to clear CPU/RAM without altering application state.
*   **System-Level Telemetry Mitigation:** Direct integration with the Windows NT Service Control API (`sc.exe`) to permanently stop and disable data-tracking components.
*   **Native Bloatware Purge via Winget:** Uses asynchronous subprocess pipelines to trigger silent, unattended software uninstallation directly through the official Windows Package Manager (`winget`).
*   **Registry-Based Startup Optimization:** Inspects and cleans `HKEY_CURRENT_USER` and `HKEY_LOCAL_MACHINE` run keys to drastically accelerate system boot times.

---

## 🛠️ Software Architecture & Design Patterns

*   **Multithreading Architecture (`threading`):** All continuous monitoring, I/O bound tasks, and AI operations run decoupled from the main thread to prevent UI freezing and ensure a smooth, deterministic user experience.
*   **Atomic State Persistence (JSON Buffer):** Implements safe transactional writes using temporary files (`.tmp`) before replacing active system configurations, avoiding corruption during unexpected power cutoffs or abrupt process terminations.
*   **Win32 API Binding (`ctypes`):** Interrogates system security tokens dynamically to evaluate context privileges (Admin vs Limited Access Mode).

---

## 📦 Installation & Setup Instructions

Follow these steps carefully to deploy, configure, and run the suite natively on your Windows environment:

### Prerequisites
1.  **Operating System:** Windows 10 / 11 (Windows 11 highly recommended).
2.  **Permissions:** Administrator privileges are mandatory to edit the registry, modify Windows services, and trigger `winget`.
3.  **Python Environment:** Python 3.10 or higher installed and properly added to your system `PATH`.
4.  **Google Account:** A valid Google account to access AI development tools.

### Step 1: Clone the Repository
Open your terminal or command prompt and clone the project:
```bash
git clone [https://github.com/your-username/w11-ramoptimizer-core.git](https://github.com/your-username/w11-ramoptimizer-core.git)
cd w11-ramoptimizer-core
```
### Step 2: Install All Requirements & Dependencies
Before executing the script, you must install all the required library dependencies. Run the following command:
```Bash
pip install customtkinter psutil google-generativeai
```
### Step 3: Get your Google AI Studio API Key
This application requires an active connection to the Gemini LLM models:

Go to Google AI Studio.

Log in using your Google account.

Click on "Get API key" and create a new API key for your project.

Copy the generated key token.

### Step 4: Configure the API Key in the Source Code
Open the application main script file using any text editor or IDE (such as VS Code or Notepad).

Go directly to Line 18, where you will find the following global configuration statement:

```
API_KEY = "PUT_YOUR_API_KEY_HERE"
```
Replace "PUT_YOUR_API_KEY_HERE" with your actual Google AI Studio API Key. Ensure that you keep the quotation marks around the token.

### Step 5: Run the Application
To ensure full functionality (handling Windows Services, registry permissions, and background installations), open an Elevated Command Prompt (Run as Administrator) and execute:
```Bash
python main.py
```
🖥️ UI Overview (Expert & Non-Expert Friendly)
The application balances a clean interface built on customtkinter with real-time feedback loops:

For Everyday Users: Simple visual indicators (🔒 / 🔓), safety profile selection (Gamer Mode, Turbo Mode), automated "Fix-all" actions, and hover-triggered tooltips explaining what each component does.

For Power Users & SysAdmins: An integrated console displaying raw subprocess outputs, terminal logging, precise PID structures, exact memory footprints (RSS mapped in Megabytes), and internal Windows service names.

👨‍💻 About the Author

I am a Systems Engineer specializing in systems programming. I am currently scaling my portfolio towards a Master's Degree in Artificial Intelligence at UCLM (Universidad de Castilla-La Mancha) with the long-term career milestone of becoming an ML Engineer and ML Architect. This project serves as a conceptual synthesis demonstrating how advanced AI heuristics can seamlessly govern and secure deterministic native systems.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
