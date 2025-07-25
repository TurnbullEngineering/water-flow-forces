# Water Flow Forces Calculator

## How to Run the Application

### Step 1: Install Python
1. Go to [python.org](https://www.python.org/downloads/)
2. Download and install the latest Python version for your operating system
3. During installation, check the box that says "Add Python to PATH" (Windows) or follow the installation instructions (Mac/Linux)

### Step 2: Install Required Tools
Open a terminal/command prompt and run the following commands:

**For Windows:**
```bash
python -m pip install --upgrade pip
pip install uv
```

**For Mac/Linux:**
```bash
python3 -m pip install --upgrade pip
pip install uv
```

### Step 3: Install Dependencies
In the same terminal window, navigate to the project folder (where you'll find this README file) and run:
```bash
uv install
```

### Step 4: Run the Application
Once dependencies are installed, start the app with:
```bash
streamlit run main.py
```

### Step 5: Use the Application
1. A browser window will open at [http://localhost:8501](http://localhost:8501)
2. Use the sidebar to:
   - Select event type
   - Configure structure parameters
   - Adjust calculation settings
3. Upload Excel files with flood data when prompted

### Excel File Requirements
Your Excel files must contain these columns:
- `[Event Name] Event Peak Flood Depth` (water depth in meters)
- `[Event Name] Event Peak Velocity` (water speed in m/s)
- `[Event Name] Event Scour` (scour depth in meters)

### Troubleshooting
- If you see "command not found" errors, make sure you're in the correct folder
- If the app doesn't start, check that all dependencies installed successfully
- For persistent issues, try using `pip install -r requirements.txt` instead of `uv install`
