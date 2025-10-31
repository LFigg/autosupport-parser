# Data Domain Autosupport Parser - Step-by-Step User Guide

This guide walks you through using the Data Domain Autosupport Parser from download to generating reports.

## 🎯 Quick Overview

You'll learn how to:
1. Download the parser from GitHub
2. Set up the parser on your computer
3. Add .eml email files to the Process folder
4. Run the parser to generate reports
5. View your results in the Reports folder

---

## Step 1: Download the Parser

### Option A: Download Just the Zip File (Recommended for most users)

1. **Go to the GitHub repository**: https://github.com/LFigg/autosupport-parser

2. **Find the zip file**: Look for `autosupport-parser-v2.0.zip` in the file list

3. **Download the zip**:
   - Click on `autosupport-parser-v2.0.zip`
   - Click the "Download" button or "View raw"
   - Save the file to your computer (e.g., Downloads folder)

### Option B: Download Entire Repository (For developers)

1. **Go to**: https://github.com/LFigg/autosupport-parser
2. **Click the green "Code" button**
3. **Select "Download ZIP"**
4. **Save** to your computer

---

## Step 2: Extract and Set Up

1. **Navigate** to where you downloaded the file (e.g., Downloads folder)

2. **Extract the zip file**:
   - **Windows**: Right-click → "Extract All" → Choose destination
   - **macOS**: Double-click the zip file
   - **Linux**: `unzip autosupport-parser-v2.0.zip`

3. **Move to your working location** (optional but recommended):
   ```
   Example locations:
   - Windows: C:\Tools\autosupport-parser\
   - macOS: /Users/YourName/Tools/autosupport-parser/
   - Linux: /home/YourName/tools/autosupport-parser/
   ```

4. **Verify the folder structure**:
   ```
   autosupport-parser/
   ├── autosupport_parser.py      # Main program
   ├── README.md                  # Full documentation
   ├── DISTRIBUTION_README.txt    # Quick start guide
   ├── Process/                   # Put your .eml files here
   ├── Reports/                   # Generated reports appear here
   ├── LICENSE
   ├── requirements.txt
   ├── sample_data.csv
   └── sample_data.html
   ```

---

## Step 3: Check Python Requirements

1. **Open Command Prompt/Terminal**:
   - **Windows**: Press `Win + R`, type `cmd`, press Enter
   - **macOS**: Press `Cmd + Space`, type `Terminal`, press Enter
   - **Linux**: Press `Ctrl + Alt + T`

2. **Check Python version**:
   ```bash
   python --version
   ```
   or
   ```bash
   python3 --version
   ```

3. **Required**: Python 3.8 or higher
   - If you don't have Python 3.8+, download from: https://python.org

4. **Navigate to the parser directory**:
   ```bash
   cd /path/to/your/autosupport-parser
   ```
   Example:
   ```bash
   # Windows
   cd C:\Tools\autosupport-parser
   
   # macOS/Linux
   cd /Users/YourName/Tools/autosupport-parser
   ```

---

## Step 4: Prepare Your Email Files

1. **Collect your .eml files**:
   - Export autosupport emails from your email client as .eml files
   - **Outlook**: Select email → File → Save As → Choose "Outlook Message Format (*.msg)" or use an .eml converter
   - **Thunderbird**: Right-click email → "Save As" → Choose location
   - **Gmail**: Use Google Takeout or third-party tools to export as .eml
   - **Other clients**: Look for "Export" or "Save As" options

2. **Copy .eml files to Process folder**:
   ```
   Example .eml files:
   Process/
   ├── Fw- scheduled autosupport (ddbackup01.example.com).eml
   ├── Daily autosupport - ddwest02.eml
   ├── Re- Autosupport ddeast01.eml
   └── autosupport-dduk01.eml
   ```

3. **File naming doesn't matter** - the parser extracts hostname and date from the email content

---

## Step 5: Run the Parser

### Basic Usage (Console Output)

1. **Open Terminal/Command Prompt** in the parser directory

2. **Run the basic command**:
   ```bash
   python autosupport_parser.py Process/
   ```

3. **View results** displayed in the terminal

### Generate CSV Reports (Recommended)

1. **Run with CSV output**:
   ```bash
   python autosupport_parser.py Process/ --format csv --output Reports/
   ```

2. **What happens**:
   - Parser processes all .eml files in Process/ folder
   - Creates CSV files in Reports/ folder
   - Organizes files by system location
   - Uses unique filenames (hostname_date_data.csv)

### Generate HTML Reports (Best for Viewing)

1. **Run with HTML output**:
   ```bash
   python autosupport_parser.py Process/ --format html --output Reports/
   ```

2. **What happens**:
   - Parser processes all .eml files in Process/ folder
   - Creates HTML files in Reports/ folder
   - Organizes files by system location
   - Creates styled reports viewable in web browsers

---

## Step 6: View Your Results

### Console Output Example
```
================================================================================
AUTOSUPPORT PARSING RESULTS
================================================================================

--- Entry 1 ---
GENERATED_ON        : Mon Oct 28 08:15:30 EST 2025
SYSTEM_SERIALNO     : DD2401000123
HOSTNAME            : ddbackup01.example.local
LOCATION            : NYC
...
```

### CSV Output Location
```
Reports/
├── NYC/
│   ├── ddbackup01_10282025_data.csv     # From Oct 28, 2025 email
│   └── ddbackup02_10272025_data.csv     # From Oct 27, 2025 email
├── LAX/
│   ├── ddwest01_10282025_data.csv
│   └── ddwest02_10282025_data.csv
└── unknown_location/
    └── ddunknown_10282025_data.csv
```

### HTML Output Location
```
Reports/
├── NYC/
│   ├── ddbackup01_10282025_data.html    # Styled web report
│   └── ddbackup02_10272025_data.html
├── LAX/
│   ├── ddwest01_10282025_data.html
│   └── ddwest02_10282025_data.html
└── unknown_location/
    └── ddunknown_10282025_data.html
```

---

## Step 7: Open and Review Reports

### For CSV Files:
1. **Navigate** to Reports/ folder
2. **Open CSV files** with:
   - Microsoft Excel
   - Google Sheets
   - LibreOffice Calc
   - Any text editor

### For HTML Files:
1. **Navigate** to Reports/ folder
2. **Double-click** any .html file
3. **Opens in your default web browser**
4. **Print or save as PDF** if needed

---

## 🔧 Troubleshooting

### Common Issues and Solutions

**Issue**: "python: command not found"
- **Solution**: Try `python3` instead of `python`
- **Or**: Install Python 3.8+ from python.org

**Issue**: No .eml files being processed
- **Solution**: Ensure .eml files are in the Process/ folder
- **Check**: File extensions are exactly ".eml" (not .msg or .txt)

**Issue**: "Permission denied" error
- **Solution**: Make sure you have write access to the Reports/ folder
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Check folder permissions

**Issue**: Empty or incorrect output
- **Solution**: Verify .eml files contain autosupport data
- **Check**: Open .eml file in text editor to see if autosupport data is present

**Issue**: Files not organized by location
- **Solution**: This is normal if systems don't have LOCATION field in autosupport
- **Result**: Files will go to "unknown_location" folder

---

## 💡 Pro Tips

### Batch Processing Multiple Sessions
```bash
# Process multiple folders
python autosupport_parser.py Process/week1/ --format html --output Reports/week1/
python autosupport_parser.py Process/week2/ --format html --output Reports/week2/
```

### Mixed File Processing
- **You can mix .tar.gz and .eml files** in the same Process/ folder
- Parser automatically detects and processes both types

### Filename Benefits
- **Date suffixes prevent overwrites** when processing multiple emails from same system
- **Location folders organize by datacenter** for easy management

### Quick Verification
```bash
# See what files are ready to process
ls Process/*.eml

# Check output after processing
ls -la Reports/*/
```

---

## 📚 What the Parser Extracts

The parser extracts comprehensive information including:

- **System Information**: Serial numbers, model, hostname, location
- **Services Status**: NFS, CIFS, NDMP, Cloud Tier, Replication
- **Storage Usage**: Active tier, cloud tier, total usage with capacity metrics
- **Compression Statistics**: Performance metrics across time periods
- **Mtree Analysis**: Filesystem analysis with retention and replication info
- **Cloud Configuration**: Profiles and data movement policies (when enabled)

---

## 🎯 Complete Example Workflow

1. **Download** `autosupport-parser-v2.0.zip` from GitHub
2. **Extract** to `C:\Tools\autosupport-parser\` (Windows example)
3. **Copy** 5 .eml files to `Process/` folder
4. **Open** Command Prompt in parser directory
5. **Run**: `python autosupport_parser.py Process/ --format html --output Reports/`
6. **Open** `Reports/` folder
7. **Navigate** to location subfolders (e.g., `NYC/`, `LAX/`)
8. **Double-click** .html files to view in browser
9. **Review** system information, storage usage, and analysis

**Result**: Professional HTML reports organized by location, ready for analysis or sharing with management!

---

## 🆘 Getting Help

- **Full Documentation**: See `README.md` in the parser folder
- **GitHub Issues**: https://github.com/LFigg/autosupport-parser/issues
- **Sample Data**: Check `sample_data.html` to see example output format