# Autosupport Parser

A Python application to extract and parse Data Domain autosupport data from tar.gz archives and .eml email files.

## Features

- **Multiple Input Sources**: Process Data Domain autosupport files from:
  - **tar.gz support bundles**: Traditional autosupport archive files
  - **.eml email files**: Email attachments containing autosupport data
  - **Mixed directories**: Process both file types in the same directory
- **Advanced File Processing**: 
  - Automatic extraction from tar.gz archives
  - Email parsing with multipart message handling
  - Robust encoding detection and handling
- **Smart Output Organization**: 
  - Location-based subdirectory organization
  - Unique filename generation prevents conflicts
  - Hostname-based naming with date suffixes for .eml files
- **Multiple output formats**: Console display, CSV export, or HTML reports
- **Comprehensive data extraction**: Extracts essential system information, storage metrics, and mtree analysis

## Extracted Fields

The parser extracts comprehensive Data Domain system information and organizes it into the following categories:

### System Information
- `GENERATED_ON` - When the autosupport was generated
- `SYSTEM_SERIALNO` - System serial number  
- `DELL_SERVICETAG` - Dell service tag
- `MODEL_NO` - Model number
- `HOSTNAME` - System hostname
- `LOCATION` - System location

### Services Status
- `NFS` - Network File System status (Enabled/Disabled/Unknown)
- `CIFS` - Common Internet File System status (Enabled/Disabled/Unknown)
- `NDMP` - Network Data Management Protocol status (Enabled/Disabled/Unknown)
- `CLOUD_TIER` - Cloud tiering functionality status (Enabled/Disabled/Unknown)
- `REPLICATION` - Data replication status (Enabled/Disabled/Configured/Unknown)

### Storage Usage Tables
Three comprehensive storage usage tables with capacity metrics:

#### Active Tier Usage
- Resource breakdown: `/data: pre-comp`, `/data: post-comp`, `/ddvar`, `/ddvar/core`
- Capacity metrics: Size GiB, Used GiB, Available GiB, Usage %, Cleanable GiB
- Cleaning estimates and timestamps

#### Cloud Tier Usage  
- Cloud storage capacity utilization (when Cloud Tier is enabled)
- Pre-comp and post-comp cloud storage metrics
- Cloud-specific capacity licensing information

#### Total Usage
- Combined storage across all tiers
- Aggregate capacity and utilization metrics
- Overall system storage summary

### Compression Statistics Tables
Detailed compression performance metrics across different time periods:

#### Active Tier Compression Stats
- Compression ratios: Global, Local, and Total compression factors
- Time-based metrics: Currently Used, Last 7 days, Last 24 hours
- Pre-comp and post-comp data volumes
- Reduction percentages

#### Cloud Tier Compression Stats
- Cloud-specific compression performance (when enabled)
- Same time-based breakdown as Active Tier
- Cloud storage efficiency metrics

#### Currently Used Summary
- Combined compression statistics across all tiers
- Overall system compression effectiveness

### Mtree Analysis Tables
Comprehensive mtree (filesystem) analysis with multiple data perspectives:

#### Mtree List
- Complete inventory of all mtrees with status information
- **Retention Lock Integration**: Compliance and governance settings
  - Retention lock status (enabled/disabled)
  - Lock mode (governance/compliance)
  - Minimum and maximum retention periods
- **Replication Information**: Cross-site data protection status
  - Replication mode (source/destination/N/A)
  - Replication host relationships
  - Replication enabled status
- Pre-compression size and operational status for each mtree

#### Mtree Active Tier Compression
- Per-mtree compression statistics for active tier storage
- **Separated Metrics**: Total compression and reduction percentages split into distinct columns
- Time-based compression analysis (24-hour and 7-day periods)
- Individual mtree compression performance

#### Mtree Cloud Tier Compression  
- Per-mtree compression statistics for cloud tier storage (when enabled)
- Same detailed breakdown as Active Tier compression
- Cloud-specific compression efficiency per mtree

### Cloud Tier Configuration (when enabled)
Advanced cloud integration settings and profiles:

#### Cloud Profiles
- **Multiple Profile Support**: Handles multiple cloud connection profiles
- Profile configuration details:
  - Profile Name: Identifier for the cloud configuration
  - Provider: Cloud service provider (e.g., ECS, AWS, Azure)  
  - Endpoint: Cloud service connection URL
  - Version: Cloud connector version information
  - Proxy Settings: Proxy host, port, and username configuration
- **Enhanced Parsing**: Robust handling of various cloud profile formats

#### Cloud Data-Movement Configuration
- Per-mtree cloud tiering policies and settings
- Data movement rules: app-managed, age-threshold policies
- Policy values: retention periods, movement schedules
- Target cloud unit assignments

### Source Information
- `SOURCE_FILE` - Original autosupport filename within the tar.gz
- `SOURCE_TAR` - Name of the source tar.gz bundle file

## Requirements

- **Python 3.8+** (required for enhanced tarfile security features)
- **Standard Library Only** - No external dependencies required
- **Email Support** - Built-in email parsing capabilities using standard library modules

## Installation

1. Ensure you have Python 3.8+ installed
2. No additional package installation required (uses only standard library modules)

## Usage

### Input File Types

The parser supports multiple input file types and automatically detects the format:

#### tar.gz Support Bundles (Traditional)
```bash
# Process a single support bundle
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz --format html
```

#### .eml Email Files (NEW)
```bash
# Process a single email file containing autosupport data
python autosupport_parser.py "Fw- scheduled autosupport (ddbackup01.example.com).eml" --format csv

# Process with custom output directory
python autosupport_parser.py autosupport-email.eml --format html --output ./reports
```

#### Mixed Directory Processing
```bash
# Process directory containing both .tar.gz and .eml files
python autosupport_parser.py /path/to/mixed-files --format csv

# Process current directory with mixed file types
python autosupport_parser.py . --format html --output ./reports
```

### Basic Usage

```bash
# Display results in console (default) - works with any file type
python autosupport_parser.py /path/to/file_or_directory

# Export to CSV format - supports .tar.gz and .eml files
python autosupport_parser.py /path/to/support-bundle.tar.gz --format csv
python autosupport_parser.py /path/to/autosupport.eml --format csv

# Export to HTML format - comprehensive reports for any input
python autosupport_parser.py /path/to/support-bundle.tar.gz --format html
python autosupport_parser.py /path/to/autosupport.eml --format html

# Process with custom output directory
python autosupport_parser.py /path/to/input --format html --output ./reports

# Process all supported files in a directory
python autosupport_parser.py /path/to/directory --format csv

# Process directory with HTML output to a different folder
python autosupport_parser.py /path/to/autosupport-files --format html --output ./analysis-reports
```

### Command Line Options

```
usage: autosupport_parser.py [-h] [--format {console,csv,html}] [--output OUTPUT] [--version] input_path

positional arguments:
  input_path            Path to supported file or directory containing supported files
                        Supported file types:
                        • .tar.gz - Data Domain support bundle archives
                        • .eml - Email files containing autosupport data
                        • Directory - Process all supported files in directory

options:
  -h, --help            show this help message and exit
  --format, -f {console,csv,html}
                        Output format (default: console)
                        • console: Display results in terminal
                        • csv: Export to CSV files with location-based organization
                        • html: Generate styled HTML reports
  --output, -o OUTPUT   Output directory for files (default: current directory)
  --version, -v         show program's version number and exit
```

## Examples

### Single File Processing

#### tar.gz Support Bundles
```bash
# Process a single support bundle with console output (default)
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz

# Export to CSV in current directory
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz --format csv

# Generate HTML report in current directory  
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz --format html

# Generate HTML report in custom directory
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz --format html --output ./reports
```

#### .eml Email Files
```bash
# Process a single email file with console output
python autosupport_parser.py "Fw- scheduled autosupport (ddbackup01.example.com).eml"

# Export email autosupport to CSV (creates ddbackup01_10282025_data.csv)
python autosupport_parser.py "autosupport-ddwest02.eml" --format csv

# Generate HTML report from email file
python autosupport_parser.py "Re- Daily autosupport.eml" --format html

# Process email with custom output directory
python autosupport_parser.py "autosupport.eml" --format html --output ./email-reports
```

### Directory Processing

#### Mixed File Types (tar.gz and .eml)
```bash
# Process all supported files in current directory to CSV
python autosupport_parser.py . --format csv

# Process mixed directory with both .tar.gz and .eml files
python autosupport_parser.py /path/to/autosupport-files --format csv --output ./results

# Process directory containing emails and bundles to HTML reports
python autosupport_parser.py /home/admin/mixed-autosupport/ --format html --output ./analysis-reports

# Process current directory to HTML reports
python autosupport_parser.py . --format html --output ./executive-reports
```

#### Traditional Bundle Processing
```bash
# Process all tar.gz files in specific directory
python autosupport_parser.py /path/to/bundles --format csv --output ./results

# Process directory of autosupport bundles to HTML reports
python autosupport_parser.py /home/admin/autosupport-bundles --format html --output ./analysis-reports
```

### Real-World Scenarios

```bash
# Daily analysis: Process today's autosupport files (mixed types) to HTML reports
python autosupport_parser.py /var/log/dd-autosupport/2025-10-28/ --format html --output ./daily-reports

# Email-only processing: Handle forwarded autosupport emails
python autosupport_parser.py /shared/email-exports/ --format csv --output ./email-analysis

# Mixed source analysis: Process both bundles and emails together
python autosupport_parser.py /shared/autosupport/ --format html --output /shared/reports/dd-analysis

# Bulk data analysis: Export all data to CSV for spreadsheet analysis
python autosupport_parser.py /archive/all-autosupport-sources/ --format csv --output ./data-export

# Executive summary: Generate clean HTML reports for management review
python autosupport_parser.py /incoming/autosupport-data/ --format html --output /shared/reports/executive
```

## Output Formats

The parser supports three output formats, each optimized for different use cases:

### Console Output (Default)

When using console format, the parser displays structured information for each autosupport file directly in the terminal:

```
================================================================================
AUTOSUPPORT PARSING RESULTS
================================================================================

--- Entry 1 ---
GENERATED_ON        : Mon Oct 28 08:15:30 EST 2025
SYSTEM_SERIALNO     : DD2401000123
DELL_SERVICETAG     : ABC1234
MODEL_NO            : DD9400
HOSTNAME            : ddbackup01.example.local
LOCATION            : NYC

SERVICES            :
  NFS               : Enabled
  CIFS              : Disabled
  NDMP              : Disabled
  CLOUD_TIER        : Enabled
  REPLICATION       : Enabled


STORAGE USAGE:

Active Tier:
         Resource         Size GiB         Used GiB        Avail GiB             Use%    Cleanable GiB
  /data: pre-comp              N/A        8450123.0              N/A              N/A              N/A
  /data: post-comp         850000.0         680000.0         170000.0              80%          12345.0
           /ddvar             50.0             18.5             31.5              37%              N/A
      /ddvar/core           1200.0              4.2           1195.8               0%              N/A
  * Estimated based on last cleaning of 2025/10/26 14:20:15.

Cloud Tier:
         Resource         Size GiB         Used GiB        Avail GiB             Use%    Cleanable GiB
  /data: pre-comp              N/A        2450000.0              N/A              N/A              N/A
  /data: post-comp         500000.0         350000.0         150000.0              70%              5.2
  * Post-comp size is based on CLOUDTIER-CAPACITY license and might not be same as the cloud storage.

Total:
         Resource         Size GiB         Used GiB        Avail GiB             Use%    Cleanable GiB
  /data: pre-comp              N/A       10900123.0              N/A              N/A              N/A
  /data: post-comp        1350000.0        1030000.0         320000.0              76%          12350.2
           /ddvar             50.0             18.5             31.5              37%              N/A
      /ddvar/core           1200.0              4.2           1195.8               0%              N/A

SOURCE_FILE         : autosupport
SOURCE_TAR          : ddbackup01-support-bundle-20251028.tar.gz
```

### CSV Output

CSV files are generated with intelligent naming conventions based on the input source:

#### File Naming Conventions
- **tar.gz files**: `{hostname_prefix}_data.csv`
  - Example: `ddbackup01_data.csv`
- **.eml files**: `{hostname_prefix}_{date}_data.csv`
  - Example: `ddbackup01_10282025_data.csv`
  - Date format: MMDDYYYY (extracted from GENERATED_ON field)
  - **Prevents filename conflicts** when multiple .eml files exist for the same system

#### Unique Filename Benefits
- **Multiple emails per system**: Each email gets a unique filename with date suffix
- **Mixed processing**: tar.gz and .eml files can coexist without conflicts
- **Chronological organization**: Date-based naming helps track autosupport timeline

The CSV contains all extracted fields plus source file information in a vertical format for basic data, and tabular format for storage tables:

```csv
Field,Value
GENERATED_ON,Mon Oct 28 08:15:30 EST 2025
SYSTEM_SERIALNO,DD2401000123
DELL_SERVICETAG,ABC1234
MODEL_NO,DD9400
HOSTNAME,ddbackup01.example.local
LOCATION,NYC

SERVICES,
NFS,Enabled
CIFS,Disabled
NDMP,Disabled
CLOUD_TIER,Enabled
REPLICATION,Enabled

STORAGE USAGE,

Active Tier,
Resource,Size GiB,Used GiB,Avail GiB,Use%,Cleanable GiB
/data: pre-comp,N/A,8450123.0,N/A,N/A,N/A
/data: post-comp,850000.0,680000.0,170000.0,80%,12345.0
/ddvar,50.0,18.5,31.5,37%,N/A
/ddvar/core,1200.0,4.2,1195.8,0%,N/A
Note:,* Estimated based on last cleaning of 2025/10/26 14:20:15.

SOURCE_FILE,autosupport
SOURCE_TAR,ddbackup01-support-bundle-20251028.tar.gz
```

### HTML Output Format

HTML format generates styled reports that can be viewed in any web browser:

```bash
# Generate HTML report
python autosupport_parser.py ddbackup01-support-bundle-20251028.tar.gz --format html
```

**HTML Features:**
- **Clean Styling**: Modern interface with responsive design
- **Color-Coded Tables**: System information, services, and storage data clearly organized
- **Proper Alignment**: Column headers centered, row labels left-justified, data right-justified
- **Hover Effects**: Interactive table rows with hover highlighting
- **Complete Data Coverage**: All fields from CSV output with enhanced presentation
- **Location Organization**: Files organized in subdirectories by location (same as CSV)
- **Browser Compatibility**: Works in all modern web browsers
- **Print Friendly**: Optimized for printing and PDF export

**HTML File Structure:**
```
output_directory/
├── NYC/
│   ├── ddbackup01_data.html           # From tar.gz bundle
│   └── ddbackup01_10282025_data.html  # From .eml file (with date)
├── DFW/
│   ├── ddwest01_data.html             # From tar.gz bundle
│   ├── ddwest01_10272025_data.html    # From .eml file (Oct 27)
│   └── ddwest01_10282025_data.html    # From .eml file (Oct 28)
└── SJC/
    └── ddbackup03_data.html           # From tar.gz bundle
```

**Filename Benefits:**
- **No conflicts**: Multiple autosupport sources per system supported
- **Clear chronology**: Date suffixes help track autosupport history
- **Source identification**: Easy to distinguish between bundle and email sources

The HTML output includes the same comprehensive data as CSV format but with clean presentation suitable for management reports and documentation.

### Location-Based Organization

When processing multiple autosupport files, output is automatically organized by location:

**Directory Structure:**
```
output_directory/
├── NYC/
│   ├── ddbackup01_data.csv              # From tar.gz bundle
│   ├── ddbackup01_10282025_data.csv     # From .eml file
│   └── ddbackup02_10272025_data.csv     # From .eml file
├── LAX/
│   ├── ddwest01_data.csv                # From tar.gz bundle
│   ├── ddwest01_10272025_data.csv       # From .eml file (Oct 27)
│   ├── ddwest01_10282025_data.csv       # From .eml file (Oct 28)
│   └── ddwest02_data.csv                # From tar.gz bundle
├── London_Office/
│   └── dduk01_10282025_data.csv         # From .eml file
└── unknown_location/
    └── unknown_host_10282025_data.csv   # From .eml file (no location)
```

**Features:**
- Each system's `LOCATION` field determines the subdirectory
- Systems from the same location are grouped together
- Location names are sanitized for filesystem compatibility
- Special characters (`<>:"/\|?*`) are replaced with underscores
- Spaces are converted to underscores
- Missing or empty locations use `unknown_location` folder

**Location Summary Output:**
```
Location-based organization summary:
  📁 NYC/ (3 files)
    📄 ddbackup01_data.csv              [tar.gz]
    📄 ddbackup01_10282025_data.csv     [.eml]
    � ddbackup02_10272025_data.csv     [.eml]
  �📁 LAX/ (4 files)
    📄 ddwest01_data.csv                [tar.gz]
    📄 ddwest01_10272025_data.csv       [.eml]
    📄 ddwest01_10282025_data.csv       [.eml]
    📄 ddwest02_data.csv                [tar.gz]
```

**Mixed Source Processing Features:**
- **Automatic detection**: Parser recognizes .tar.gz and .eml files automatically
- **Unified processing**: Both file types processed with same data extraction logic
- **Intelligent organization**: Files grouped by location regardless of source type
- **Conflict prevention**: Date-based naming ensures no filename collisions

## File Structure and Input Formats

### tar.gz Support Bundles
The parser expects tar.gz files containing Data Domain support bundles with autosupport files located at:
```
ddr/var/support/autosupport
```

### .eml Email Files
The parser handles .eml email files containing autosupport data in various formats:

#### Email Structure Support
- **Multipart messages**: Handles complex email structures with multiple parts
- **Plain text content**: Extracts autosupport data from email body text
- **Encoding handling**: Automatically detects and handles various text encodings
- **Header parsing**: Extracts metadata from email headers when available

#### Email Content Formats
- **Inline autosupport data**: Autosupport content directly in email body
- **Forwarded emails**: Handles "Fw:" and "Re:" email chains
- **Scheduled autosupport**: Processes automated autosupport email reports
- **Manual exports**: Supports manually exported .eml files from email clients

#### Email File Sources
- **Outlook exports**: .eml files exported from Microsoft Outlook
- **Thunderbird exports**: .eml files from Mozilla Thunderbird  
- **Web email exports**: .eml files from web-based email clients
- **Email server exports**: Direct .eml exports from email servers

## Error Handling

The parser includes comprehensive error handling for various scenarios:

### File Processing Errors
- **Missing fields**: Fields are marked as 'N/A' in the output when not found
- **Extraction errors**: Individual file errors are reported but don't stop batch processing
- **Invalid tar.gz files**: Corrupted or invalid archives are skipped with error messages
- **Email parsing errors**: Malformed .eml files are skipped with descriptive error messages

### Email-Specific Error Handling
- **Encoding issues**: Automatically tries multiple encodings for email content
- **Malformed emails**: Gracefully handles emails with missing or corrupted headers
- **Empty content**: Reports when .eml files contain no parseable autosupport data
- **Multipart complexity**: Handles complex email structures with nested parts

### Data Extraction Resilience
- **Partial data**: Successfully processes files even when some data sections are missing
- **Format variations**: Handles variations in autosupport data formatting
- **Date parsing**: Robust date parsing with fallbacks for various timestamp formats
- **Hostname extraction**: Multiple methods to extract hostname information

### Processing Continuity
- **Batch processing**: Individual file failures don't interrupt directory processing
- **Mixed file types**: Processing continues even when some files are unsupported formats
- **Permission issues**: Clear error messages for file access problems
- **Output directory creation**: Automatically creates output directories as needed

## Extending the Parser

To add new fields for extraction:

1. Add the field name to the `REQUIRED_FIELDS` list in the `AutosupportParser` class
2. The parser will automatically extract any field that follows the pattern `FIELD_NAME=value` in the autosupport file

Example:
```python
REQUIRED_FIELDS = [
    'GENERATED_ON',
    'SYSTEM_SERIALNO', 
    'DELL_SERVICETAG',
    'MODEL_NO',
    'HOSTNAME',
    'LOCATION',
    'NEW_FIELD_NAME'  # Add your new field here
]
```

## Technical Notes

### File Processing
- **Multiple sources**: Handles multiple autosupport files within a single tar.gz archive
- **Mixed directories**: Processes .tar.gz and .eml files in the same directory seamlessly
- **Temporary handling**: Uses temporary directories for extraction and cleans up automatically
- **Memory efficient**: Processes files individually to handle large datasets

### Output Organization
- **Location grouping**: Files are organized by system location for better management
- **Unique naming**: Intelligent filename generation prevents conflicts between sources
- **Date integration**: .eml files include date suffixes for chronological tracking
- **Backward compatibility**: Existing tar.gz processing unchanged

### Text Processing
- **Encoding resilience**: Handles various text encodings gracefully
- **Regex optimization**: Enhanced pattern matching with performance optimizations
- **Data validation**: Comprehensive validation of extracted data
- **Format flexibility**: Adapts to variations in autosupport data formatting

### Email Processing Features
- **Standard compliance**: Uses Python's standard email library for robust parsing
- **Multipart support**: Handles complex email structures with attachments and nested parts  
- **Header extraction**: Utilizes email metadata when available
- **Content detection**: Automatically identifies autosupport data within email content

## Version

Current version: 2.0
- Added comprehensive .eml email file support
- Implemented unique filename generation for multiple sources per system
- Enhanced mixed directory processing capabilities
- Improved error handling and encoding support
- Updated Python requirements to 3.8+ for enhanced security features

## Future Enhancements

The application is designed to be easily extensible for additional features:
- **Additional email formats**: Support for .msg and other email file types
- **Cloud integration**: Direct processing from cloud storage services
- **Database output**: Direct export to database systems
- **API integration**: REST API for remote processing requests
- **Real-time monitoring**: Watch folder capabilities for automated processing