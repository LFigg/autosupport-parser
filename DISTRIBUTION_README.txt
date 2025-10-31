# Data Domain Autosupport Parser v2.0 - Distribution Package

This zip file contains everything you need to run the Data Domain Autosupport Parser.

## 📦 What's Included

- `autosupport_parser.py` - Main parser application
- `README.md` - Complete documentation and usage examples
- `requirements.txt` - Python version and dependency information
- `LICENSE` - MIT License for open source use
- `Process/` - Directory for input autosupport files (.tar.gz and .eml)
- `Reports/` - Directory for generated output reports (CSV and HTML)
- `sample_data.csv` - Sample CSV output format
- `sample_data.html` - Sample HTML output format

## 🚀 Quick Start

1. **Extract this zip file** to your desired location
2. **Ensure Python 3.8+** is installed on your system
3. **Place your autosupport files** in the `Process/` directory
4. **Run the parser**:
   ```bash
   python autosupport_parser.py Process/ --format html --output Reports/
   ```

## 📖 Full Documentation

See `README.md` for complete documentation including:
- Detailed usage examples
- Command line options
- Email file (.eml) support
- Mixed directory processing
- Output format descriptions
- Error handling information

## 🔗 Source Code

Latest version and source code available at:
https://github.com/LFigg/autosupport-parser

## 📋 System Requirements

- Python 3.8 or higher
- No external dependencies required (uses standard library only)
- Compatible with Windows, macOS, and Linux

## 💡 Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/LFigg/autosupport-parser/issues
- Source Code: https://github.com/LFigg/autosupport-parser