#!/usr/bin/env python3
"""
Autosupport Parser - Extract and parse Data Domain autosupport files
Author: Automated Tool
Date: October 2025

This application extracts autosupport files from tar.gz archives and parses
key system information for analysis and reporting.
"""

import argparse
import csv
import email
import os
import re
import tarfile
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class AutosupportParser:
    """Parser for Data Domain autosupport files"""
    
    # Fields to extract from autosupport files
    REQUIRED_FIELDS = [
        'GENERATED_ON',
        'SYSTEM_SERIALNO', 
        'DELL_SERVICETAG',
        'MODEL_NO',
        'HOSTNAME',
        'LOCATION'
    ]
    
    # Services to check
    SERVICES = [
        'NFS',
        'CIFS',
        'NDMP',
        'CLOUD_TIER',
        'REPLICATION'
    ]
    
    def __init__(self):
        self.parsed_data = []
    
    def extract_tar_gz(self, tar_path: str, temp_dir: str) -> List[str]:
        """
        Extract tar.gz file and find autosupport files
        
        Args:
            tar_path: Path to the tar.gz file
            temp_dir: Temporary directory for extraction
            
        Returns:
            List of paths to extracted autosupport files
        """
        autosupport_files = []
        
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                # Extract all files (filter='data' maintains current behavior and suppresses warning)
                tar.extractall(path=temp_dir, filter='data')
                
                # Look for autosupport files in the expected location
                support_dir = os.path.join(temp_dir, 'ddr', 'var', 'support')
                if os.path.exists(support_dir):
                    # Find the main autosupport file (without extension)
                    autosupport_path = os.path.join(support_dir, 'autosupport')
                    if os.path.exists(autosupport_path):
                        autosupport_files.append(autosupport_path)
                    
                    # Also check for numbered autosupport files
                    for file in os.listdir(support_dir):
                        if re.match(r'^autosupport$', file) and file not in [os.path.basename(f) for f in autosupport_files]:
                            full_path = os.path.join(support_dir, file)
                            if os.path.isfile(full_path):
                                autosupport_files.append(full_path)
                
        except Exception as e:
            print(f"Error extracting {tar_path}: {e}")
            
        return autosupport_files
    
    def extract_autosupport_from_eml(self, eml_path: str, temp_dir: str) -> List[str]:
        """
        Extract autosupport content from .eml email files
        
        Args:
            eml_path: Path to .eml file
            temp_dir: Temporary directory for extraction
            
        Returns:
            List of paths to extracted autosupport content files
        """
        autosupport_files = []
        
        try:
            with open(eml_path, 'r', encoding='utf-8', errors='ignore') as eml_file:
                msg = email.message_from_file(eml_file)
                
            # Extract autosupport content from email body
            autosupport_content = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        body = part.get_payload(decode=True)
                        if body:
                            if isinstance(body, bytes):
                                body_text = body.decode('utf-8', errors='ignore')
                            else:
                                body_text = str(body)
                            # Check if this part contains autosupport data
                            if 'GENERATED_ON=' in body_text and 'SYSTEM_SERIALNO=' in body_text:
                                autosupport_content = body_text
                                break
            else:
                # Single part message
                body = msg.get_payload(decode=True)
                if body:
                    if isinstance(body, bytes):
                        body_text = body.decode('utf-8', errors='ignore')
                    else:
                        body_text = str(body)
                    if 'GENERATED_ON=' in body_text and 'SYSTEM_SERIALNO=' in body_text:
                        autosupport_content = body_text
            
            if autosupport_content:
                # Create temporary autosupport file
                eml_basename = os.path.splitext(os.path.basename(eml_path))[0]
                autosupport_file = os.path.join(temp_dir, f'autosupport_{eml_basename}')
                
                with open(autosupport_file, 'w', encoding='utf-8') as f:
                    f.write(autosupport_content)
                
                autosupport_files.append(autosupport_file)
            else:
                print(f"No autosupport data found in {eml_path}")
                
        except Exception as e:
            print(f"Error parsing email {eml_path}: {e}")
            
        return autosupport_files
    
    def parse_autosupport_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an autosupport file and extract required fields
        
        Args:
            file_path: Path to the autosupport file
            
        Returns:
            Dictionary containing extracted field values
        """
        data: Dict[str, Any] = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extract each required field using regex
            for field in self.REQUIRED_FIELDS:
                pattern = rf'^{field}=(.*)$'
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    data[field] = match.group(1).strip()
                else:
                    data[field] = 'N/A'
                
            # Parse services status
            services_status = self.parse_services_status(content)
            for service, status in services_status.items():
                data[service] = status
                
            # Parse storage tables
            storage_data = self.parse_storage_tables(content)
            data['STORAGE_TABLES'] = storage_data
                
            # Parse cloud tier information if Cloud Tier is enabled
            if data.get('CLOUD_TIER') == 'Enabled':
                cloud_profiles = self.parse_cloud_profiles(content)
                cloud_movement = self.parse_cloud_data_movement(content)
                data['CLOUD_PROFILES'] = cloud_profiles
                data['CLOUD_DATA_MOVEMENT'] = cloud_movement
            else:
                data['CLOUD_PROFILES'] = []
                data['CLOUD_DATA_MOVEMENT'] = []
                        
            # Add source file information
            data['SOURCE_FILE'] = os.path.basename(file_path)
            data['SOURCE_TAR'] = getattr(self, '_current_tar', 'N/A')
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            # Return empty data with N/A values
            data = {field: 'N/A' for field in self.REQUIRED_FIELDS}
            # Add services with Unknown status
            for service in self.SERVICES:
                data[service] = 'Unknown'
            # Add empty storage tables
            data['STORAGE_TABLES'] = {}
            data['SOURCE_FILE'] = os.path.basename(file_path)
            data['SOURCE_TAR'] = getattr(self, '_current_tar', 'N/A')
            
        return data
    
    def get_hostname_prefix(self, hostname: str) -> str:
        """
        Extract hostname prefix (before first period)
        
        Args:
            hostname: Full hostname
            
        Returns:
            Hostname prefix for filename
        """
        if not hostname or hostname == 'N/A':
            return 'unknown'
        return hostname.split('.')[0]
    
    def get_date_suffix_from_generated_on(self, generated_on: str) -> str:
        """
        Extract date suffix in mmddyyyy format from GENERATED_ON field
        
        Args:
            generated_on: Generated on timestamp string
            
        Returns:
            Date suffix in mmddyyyy format
        """
        if not generated_on or generated_on == 'N/A':
            return 'unknown'
            
        try:
            # Parse various date formats commonly found in autosupport
            # Examples: "Fri Dec  6 06:16:27 EST 2024", "Fri Oct 17 06:03:20 EDT 2025"
            from datetime import datetime
            
            # Remove timezone info and extra spaces for easier parsing
            cleaned_date = re.sub(r'\s+', ' ', generated_on.strip())
            
            # Try different date format patterns
            date_patterns = [
                '%a %b %d %H:%M:%S %Z %Y',  # Fri Dec  6 06:16:27 EST 2024
                '%a %b %d %H:%M:%S %Y',     # Fri Dec  6 06:16:27 2024
                '%b %d %H:%M:%S %Z %Y',     # Dec  6 06:16:27 EST 2024
                '%b %d %H:%M:%S %Y',        # Dec  6 06:16:27 2024
            ]
            
            # Remove timezone abbreviations that might interfere
            for tz in ['EST', 'EDT', 'CST', 'CDT', 'MST', 'MDT', 'PST', 'PDT', 'UTC']:
                cleaned_date = cleaned_date.replace(f' {tz} ', ' ')
            
            parsed_date = None
            for pattern in date_patterns:
                try:
                    parsed_date = datetime.strptime(cleaned_date, pattern)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                return f"{parsed_date.month:02d}{parsed_date.day:02d}{parsed_date.year}"
            else:
                # Fallback: try to extract numbers that look like a date
                numbers = re.findall(r'\d+', generated_on)
                if len(numbers) >= 3:
                    # Assume format has month, day, year somewhere
                    month = int(numbers[1]) if len(numbers) > 1 and 1 <= int(numbers[1]) <= 12 else 1
                    day = int(numbers[2]) if len(numbers) > 2 and 1 <= int(numbers[2]) <= 31 else 1
                    year = int(numbers[-1]) if numbers else 2024
                    return f"{month:02d}{day:02d}{year}"
                    
        except Exception:
            pass
            
        return 'unknown'
    
    def get_file_identifier(self, hostname: str, generated_on: str, source_file: str) -> str:
        """
        Generate unique file identifier based on source type
        
        Args:
            hostname: System hostname
            generated_on: Generated timestamp
            source_file: Source file name
            
        Returns:
            Unique file identifier
        """
        hostname_prefix = self.get_hostname_prefix(hostname)
        
        # For .eml files, include date to make filename unique
        if source_file and (source_file.endswith('.eml') or 'autosupport_' in source_file):
            date_suffix = self.get_date_suffix_from_generated_on(generated_on)
            return f"{hostname_prefix}_{date_suffix}"
        else:
            # For .tar.gz files, use just hostname prefix
            return hostname_prefix
    
    def get_location_folder(self, location: str) -> str:
        """
        Get sanitized location name for folder creation
        
        Args:
            location: Location string from autosupport
            
        Returns:
            Sanitized location name for folder
        """
        if not location or location == 'N/A':
            return 'unknown_location'
        
        # Sanitize location name for filesystem compatibility
        # Remove/replace characters that might cause issues in folder names
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', location.strip())
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        return sanitized if sanitized else 'unknown_location'
    
    def parse_services_status(self, content: str) -> Dict[str, str]:
        """
        Parse service status from autosupport content
        
        Args:
            content: Full autosupport file content
            
        Returns:
            Dictionary containing service status
        """
        services_status = {}
        
        # NFS Status
        if re.search(r'The NFS system is currently active and running', content, re.IGNORECASE):
            services_status['NFS'] = 'Enabled'
        elif re.search(r'NFS.*disabled|NFS.*not.*running', content, re.IGNORECASE):
            services_status['NFS'] = 'Disabled'
        else:
            services_status['NFS'] = 'Unknown'
        
        # CIFS Status
        if re.search(r'CIFS is disabled', content, re.IGNORECASE):
            services_status['CIFS'] = 'Disabled'
        elif re.search(r'CIFS.*enabled|CIFS.*active', content, re.IGNORECASE):
            services_status['CIFS'] = 'Enabled'
        else:
            services_status['CIFS'] = 'Unknown'
        
        # NDMP Status
        if re.search(r'NDMP daemon admin_state: disabled', content, re.IGNORECASE):
            services_status['NDMP'] = 'Disabled'
        elif re.search(r'NDMP daemon admin_state: enabled', content, re.IGNORECASE):
            services_status['NDMP'] = 'Enabled'
        else:
            services_status['NDMP'] = 'Unknown'
        
        # Cloud Tier Status
        if re.search(r'CLOUD TIER.*:', content) or re.search(r'Cloud Unit:', content):
            services_status['CLOUD_TIER'] = 'Enabled'
        elif re.search(r'cloud.*disabled', content, re.IGNORECASE):
            services_status['CLOUD_TIER'] = 'Disabled'
        else:
            services_status['CLOUD_TIER'] = 'Unknown'
        
        # Replication Status
        if re.search(r'Enabled:\s+yes', content, re.IGNORECASE):
            services_status['REPLICATION'] = 'Enabled'
        elif re.search(r'Enabled:\s+no|replication.*disabled', content, re.IGNORECASE):
            services_status['REPLICATION'] = 'Disabled'
        elif re.search(r'Replication Status', content):
            services_status['REPLICATION'] = 'Configured'
        else:
            services_status['REPLICATION'] = 'Unknown'
        
        return services_status
    
    def parse_mtree_retention_locks(self, content: str) -> Dict[str, Dict[str, str]]:
        """
        Parse retention lock information for each mtree
        
        Args:
            content: Raw autosupport content
            
        Returns:
            Dictionary mapping mtree paths to their retention lock info
        """
        retention_locks = {}
        
        # Find all mtree retention lock sections
        pattern = r'Mtree: (/data/col1/[^\s]+)\s*\n\s*Option\s+Value\s*\n-+\s+-+\s*\n(.*?)\n-+\s+-+(?=\s*\n|$)'
        matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
        
        for mtree_path, options_section in matches:
            retention_info = {
                'Retention_Lock': 'disabled',
                'Lock_Mode': 'N/A',
                'Min_Retention_Period': 'N/A',
                'Max_Retention_Period': 'N/A'
            }
            
            # Parse the options section
            for line in options_section.strip().split('\n'):
                if not line.strip():
                    continue
                    
                # Split on multiple spaces to handle the table format
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 2:
                    option = parts[0].strip()
                    value = parts[1].strip()
                    
                    if option == 'Retention-lock':
                        # Handle values like "enabled" or "disabled (never enabled)"
                        if value.lower().startswith('enabled'):
                            retention_info['Retention_Lock'] = 'enabled'
                        else:
                            retention_info['Retention_Lock'] = 'disabled'
                            
                    elif option == 'Retention-lock mode':
                        retention_info['Lock_Mode'] = value if value != 'N/A' else 'N/A'
                        
                    elif option == 'Retention-lock min-retention-period':
                        retention_info['Min_Retention_Period'] = value
                        
                    elif option == 'Retention-lock max-retention-period':
                        retention_info['Max_Retention_Period'] = value
            
            retention_locks[mtree_path] = retention_info
        
        return retention_locks
    
    def parse_mtree_replication_info(self, content: str) -> Dict[str, Dict[str, str]]:
        """
        Parse replication information for each mtree
        
        Args:
            content: Raw autosupport content
            
        Returns:
            Dictionary mapping mtree paths to their replication info
        """
        replication_info = {}
        
        # Find all replication context sections
        pattern = r'CTX:\s+\d+\s*\n(.*?)(?=CTX:\s+\d+|Replication Options|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for section in matches:
            lines = section.strip().split('\n')
            replication_data = {
                'Mode': 'N/A',
                'Connection_Host': 'N/A', 
                'Enabled': 'N/A'
            }
            mtree_path = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Mode:'):
                    mode_value = line.split(':', 1)[1].strip()
                    replication_data['Mode'] = mode_value
                    
                elif line.startswith('Destination:'):
                    dest_value = line.split(':', 1)[1].strip()
                    # Extract mtree path from destination like: mtree://host.domain/data/col1/mtree_name
                    if '/data/col1/' in dest_value:
                        mtree_path = '/data/col1/' + dest_value.split('/data/col1/')[-1]
                        
                elif line.startswith('Connection Host:'):
                    host_value = line.split(':', 1)[1].strip()
                    # Extract just the hostname without domain
                    if '.' in host_value:
                        replication_data['Connection_Host'] = host_value.split('.')[0]
                    else:
                        replication_data['Connection_Host'] = host_value
                        
                elif line.startswith('Enabled:'):
                    enabled_value = line.split(':', 1)[1].strip()
                    replication_data['Enabled'] = enabled_value
            
            # Only add if we found a valid mtree path
            if mtree_path:
                replication_info[mtree_path] = replication_data
        
        return replication_info
    
    def parse_cloud_profiles(self, content: str) -> List[Dict[str, str]]:
        """
        Parse cloud profiles information
        
        Args:
            content: Raw autosupport content
            
        Returns:
            List of cloud profile dictionaries
        """
        cloud_profiles = []
        
        # Find Cloud Profiles section
        profiles_pattern = r'Cloud Profiles\s*\n-{10,}\s*\n(.*?)(?=\nCloud Unit List|\nCloud Data-Movement|$)'
        match = re.search(profiles_pattern, content, re.DOTALL)
        
        if match:
            profiles_section = match.group(1)
            
            # Split by Profile name to get individual profiles
            profile_blocks = re.split(r'(?=Profile name:)', profiles_section)
            
            for block in profile_blocks:
                if not block.strip() or 'Profile name:' not in block:
                    continue
                    
                profile_data = {}
                
                # Process line by line for more accurate field extraction
                lines = block.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Extract each field from its specific line
                    if line.startswith('Profile name:'):
                        profile_data['Profile_Name'] = line.split('Profile name:')[1].strip()
                    elif line.startswith('Provider:'):
                        profile_data['Provider'] = line.split('Provider:')[1].strip()
                    elif line.startswith('Endpoint:'):
                        profile_data['Endpoint'] = line.split('Endpoint:')[1].strip()
                    elif line.startswith('Version:'):
                        profile_data['Version'] = line.split('Version:')[1].strip()
                    elif line.startswith('Proxy host:'):
                        proxy_host = line.split('Proxy host:')[1].strip()
                        profile_data['Proxy_Host'] = proxy_host if proxy_host else 'N/A'
                    elif line.startswith('Proxy port:'):
                        proxy_port = line.split('Proxy port:')[1].strip()
                        profile_data['Proxy_Port'] = proxy_port if proxy_port else 'N/A'
                    elif line.startswith('Proxy username:'):
                        proxy_username = line.split('Proxy username:')[1].strip()
                        profile_data['Proxy_Username'] = proxy_username if proxy_username else 'N/A'
                
                # Set default values for any missing optional fields
                for field in ['Version', 'Proxy_Host', 'Proxy_Port', 'Proxy_Username']:
                    if field not in profile_data:
                        profile_data[field] = 'N/A'
                
                # Only add profile if we found at least the basic required fields
                if 'Profile_Name' in profile_data and 'Provider' in profile_data:
                    cloud_profiles.append(profile_data)
        
        return cloud_profiles
    
    def parse_cloud_data_movement(self, content: str) -> List[Dict[str, str]]:
        """
        Parse cloud data-movement configuration
        
        Args:
            content: Raw autosupport content
            
        Returns:
            List of cloud data-movement configuration dictionaries
        """
        cloud_movement = []
        
        # Find Cloud Data-Movement Configuration section
        movement_pattern = r'Cloud Data-Movement Configuration\s*\n-{30,}(.*?)(?=\nData-movement is scheduled)'
        match = re.search(movement_pattern, content, re.DOTALL)
        
        if match:
            movement_section = match.group(1).strip()
            
            # Parse each line of the table
            for line in movement_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('-') and not line.startswith('Mtree') and 'Target(Tier/Unit Name)' not in line:
                    # Parse fixed-width format: Mtree (28 chars), Target (26 chars), Policy (13 chars), Value (rest)
                    if len(line) > 60 and line.startswith('/data/col1/'):
                        # Extract mtree (first ~28 characters)
                        mtree = line[:28].strip()
                        remainder = line[28:].strip()
                        
                        # Extract target (next ~26 characters)  
                        target = remainder[:26].strip()
                        remainder = remainder[26:].strip()
                        
                        # Extract policy (next ~13 characters)
                        policy = remainder[:13].strip()
                        value = remainder[13:].strip()
                        
                        if mtree and target and policy and value:
                            cloud_movement.append({
                                'Mtree': mtree,
                                'Target': target,
                                'Policy': policy,
                                'Value': value
                            })
        
        return cloud_movement
    
    def parse_storage_tables(self, content: str) -> Dict[str, Any]:
        """
        Parse storage tables (Active Tier, Cloud Tier, Total) from autosupport content
        
        Args:
            content: Full autosupport file content
            
        Returns:
            Dictionary containing storage table data and notes
        """
        storage_data = {}
        
        # Define patterns for storage usage tables
        storage_usage_patterns = {
            'Active Tier Usage': r'Active Tier:\s*\nResource.*?\n(.*?)(?=\n\s*\* |\n\s*Cloud Tier|\Z)',
            'Cloud Tier Usage': r'Cloud Tier\s*\nResource.*?\n(.*?)(?=\n\s*\* |\n\s*Total:|\Z)',
            'Total Usage': r'Total:\s*\nResource.*?\n(.*?)(?=\n\s*\* |\Z)'
        }
        
        # Define patterns for compression statistics tables
        compression_patterns = {
            'Active Tier Compression': r'Active Tier:\s*\n\s*Pre-Comp.*?Total-Comp.*?\n.*?\n(.*?)(?=\n\s*\*.*?cleaning|\n\s*Cloud Tier:)',
            'Cloud Tier Compression': r'(?s)Filesys Compression.*?Cloud Tier:\s*\n.*?-{10,}\s*\n(.*?)(?=\n\s*\* Does not include)', 
            'Currently Used Summary': r'Currently Used:\*\s*\n\s*Pre-Comp.*?Total-Comp.*?\n.*?\n(.*?)(?=\n\s*Key:)'
        }
        
        # Define patterns for Mtree Show Compression tables (optimized to avoid catastrophic backtracking)
        mtree_patterns = {
            'Mtree Active Tier Compression': r'Mtree Show Compression[^\n]*\n(?:[^\n]*\n)*?Active Tier:[^\n]*\n(?:-{10,}[^\n]*\n)([^-]*?)(?:-{10,}|Cloud Tier:)',
            'Mtree Cloud Tier Compression': r'Mtree Show Compression[^\n]*\n(?:[^\n]*\n)*?Cloud Tier:[^\n]*\n(?:-{10,}[^\n]*\n)([^-]*?)(?:-{10,}|Key:)',
            'Mtree List': r'Mtree List\s*\n-{5,}\s*\nName[^\n]*Pre-Comp[^\n]*Status[^\n]*\n-{10,}[^\n]*\n((?:/data/col1/[^\n]*\n)*?)(?=-{10,}|\nMtree Options|\Z)'
        }
        
        # Combine all table patterns
        table_patterns = {**storage_usage_patterns, **compression_patterns, **mtree_patterns}
        
        # Parse retention lock data for mtrees (needed for enhanced Mtree List)
        retention_locks = self.parse_mtree_retention_locks(content)
        
        # Parse replication information for mtrees (needed for enhanced Mtree List)
        replication_info = self.parse_mtree_replication_info(content)
        
        for table_name, pattern in table_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                table_section = match.group(1)
                rows = []
                
                # Split into lines and process
                lines = table_section.strip().split('\n')
                
                # Determine table type based on name
                is_compression_table = 'Compression' in table_name or 'Currently Used' in table_name
                is_usage_table = 'Usage' in table_name
                is_mtree_table = 'Mtree' in table_name
                

                
                for line in lines:
                    # Skip separator lines and empty lines
                    if '----' in line or '-----------' in line or not line.strip():
                        continue
                    
                    # Skip header lines
                    if any(header in line for header in ['Resource', 'Size GiB', 'Pre-Comp', 'Post-Comp']):
                        continue
                    
                    # Process Mtree List table data lines
                    if is_mtree_table and 'Mtree List' in table_name and line.strip() and line.strip().startswith('/data/col1/'):
                        clean_line = re.sub(r'\*', '', line).strip()
                        
                        # Parse mtree list format using flexible space-separated columns
                        # Split on multiple spaces (2 or more) to handle variable-length names
                        parts = re.split(r'\s{2,}', clean_line)
                        if len(parts) >= 3:
                            mtree_name = parts[0].strip()
                            pre_comp_size = parts[1].strip()
                            status = parts[2].strip()
                            
                            # Get retention lock info for this mtree
                            retention_info = retention_locks.get(mtree_name, {
                                'Retention_Lock': 'N/A',
                                'Lock_Mode': 'N/A',
                                'Min_Retention_Period': 'N/A',
                                'Max_Retention_Period': 'N/A'
                            })
                            
                            # Get replication info for this mtree
                            repl_info = replication_info.get(mtree_name, {
                                'Mode': 'N/A',
                                'Connection_Host': 'N/A',
                                'Enabled': 'N/A'
                            })
                            
                            row = {
                                'Name': mtree_name,
                                'Pre_Comp_GiB': pre_comp_size,
                                'Status': status,
                                'Retention_Lock': retention_info['Retention_Lock'],
                                'Lock_Mode': retention_info['Lock_Mode'],
                                'Min_Retention_Period': retention_info['Min_Retention_Period'],
                                'Max_Retention_Period': retention_info['Max_Retention_Period'],
                                'Replication_Mode': repl_info['Mode'],
                                'Replication_Host': repl_info['Connection_Host'],
                                'Replication_Enabled': repl_info['Enabled']
                            }
                            rows.append(row)
                    
                    # Process Mtree compression table data lines (MUST come before usage table check)
                    elif is_mtree_table and line.strip() and line.strip().startswith('/data/col1/'):
                        clean_line = re.sub(r'\*', '', line).strip()
                        
                        # Parse mtree compression table format - find where numeric data starts
                        if len(clean_line) > 35:
                            # Find the position where numeric data starts (after the mtree path)
                            # Look for the first digit after spaces following the mtree path
                            match_data = re.match(r'^(/data/col1/[^\s]+)\s+(.*)', clean_line)
                            if match_data:
                                mtree_name = match_data.group(1)
                                remainder = match_data.group(2).strip()
                                values = remainder.split()
                                
                                if len(values) >= 10:  # Should have 10 values (5 for 24hrs, 5 for 7days)
                                    # Helper function to split Total(Reduction%) values
                                    def split_total_reduction(value):
                                        if '(' in value and ')' in value:
                                            total_val = value.split('(')[0]
                                            reduction_val = value.split('(')[1].rstrip(')')
                                            return total_val, reduction_val
                                        else:
                                            return value, 'N/A'
                                    
                                    # Split the Total_24hrs column
                                    total_24hrs, reduction_24hrs = split_total_reduction(values[4] if values[4] != '-' else 'N/A')
                                    
                                    # Split the Total_7days column  
                                    total_7days, reduction_7days = split_total_reduction(values[9] if values[9] != '-' else 'N/A')
                                    
                                    row = {
                                        'Mtree': mtree_name,
                                        'Pre_24hrs_GiB': values[0] if values[0] != '-' else 'N/A',
                                        'Post_24hrs_GiB': values[1] if values[1] != '-' else 'N/A',
                                        'Global_24hrs': values[2] if values[2] != '-' else 'N/A',
                                        'Local_24hrs': values[3] if values[3] != '-' else 'N/A',
                                        'Total_24hrs': total_24hrs,
                                        'Reduction_24hrs_Percent': reduction_24hrs,
                                        'Pre_7days_GiB': values[5] if values[5] != '-' else 'N/A',
                                        'Post_7days_GiB': values[6] if values[6] != '-' else 'N/A',
                                        'Global_7days': values[7] if values[7] != '-' else 'N/A',
                                        'Local_7days': values[8] if values[8] != '-' else 'N/A',
                                        'Total_7days': total_7days,
                                        'Reduction_7days_Percent': reduction_7days
                                    }
                                    rows.append(row)
                    
                    # Process usage table data lines (those starting with /)
                    elif is_usage_table and line.strip().startswith('/'):
                        # Clean the line
                        clean_line = re.sub(r'\*', '', line).strip()
                        
                        # Parse the fixed-width format
                        if len(clean_line) > 18:
                            resource = clean_line[:18].strip()
                            remainder = clean_line[18:].strip()
                            values = remainder.split()
                            
                            if values and len(values) >= 1:
                                row = {
                                    'Resource': resource,
                                    'Size_GiB': values[0] if len(values) > 0 else 'N/A',
                                    'Used_GiB': values[1] if len(values) > 1 else 'N/A', 
                                    'Avail_GiB': values[2] if len(values) > 2 else 'N/A',
                                    'Use_Percent': values[3] if len(values) > 3 else 'N/A',
                                    'Cleanable_GiB': values[4] if len(values) > 4 else 'N/A'
                                }
                                rows.append(row)
                    
                    # Process compression table data lines
                    elif is_compression_table and line.strip() and not line.strip().startswith('(') and not line.strip().startswith('Key:'):
                        clean_line = re.sub(r'\*', '', line).strip()
                        
                        # Parse compression table format
                        if ':' in clean_line or any(tier in clean_line for tier in ['Currently Used', 'Last 7 days', 'Last 24 hrs', 'Active Tier', 'Cloud Tier', 'Total', 'Written']):
                            # Split on whitespace but preserve the metric name
                            parts = clean_line.split()
                            
                            if len(parts) >= 2:
                                # First part(s) might be the metric name
                                if parts[0] in ['Currently', 'Last', 'Active', 'Cloud', 'Total', 'Written:']:
                                    if parts[0] == 'Currently' and len(parts) > 1 and parts[1] == 'Used:':
                                        metric = 'Currently Used'
                                        values = parts[2:]
                                    elif parts[0] == 'Last' and len(parts) > 2:
                                        metric = f"{parts[0]} {parts[1]} {parts[2]}"
                                        values = parts[3:]
                                    elif parts[0] in ['Active', 'Cloud']:
                                        metric = f"{parts[0]} {parts[1]}"
                                        values = parts[2:]
                                    elif parts[0] == 'Total':
                                        metric = 'Total'
                                        values = parts[1:]
                                    elif parts[0] == 'Written:':
                                        metric = 'Written'
                                        values = parts[1:]
                                    else:
                                        metric = parts[0]
                                        values = parts[1:]
                                else:
                                    metric = parts[0].rstrip(':')
                                    values = parts[1:]
                                
                                if len(values) >= 2:
                                    row = {
                                        'Metric': metric,
                                        'Pre_Comp_GiB': values[0] if len(values) > 0 else 'N/A',
                                        'Post_Comp_GiB': values[1] if len(values) > 1 else 'N/A',
                                        'Global_Comp_Factor': values[2] if len(values) > 2 else 'N/A',
                                        'Local_Comp_Factor': values[3] if len(values) > 3 else 'N/A',
                                        'Total_Comp_Factor': values[4] if len(values) > 4 else 'N/A'
                                    }
                                    rows.append(row)
                
                storage_data[table_name] = rows
                
                # Look for note after this table
                note_start = content.find(table_section) + len(table_section)
                note_section = content[note_start:note_start + 500]  # Look ahead for note
                
                note_lines = []
                for line in note_section.split('\n'):
                    if line.strip().startswith('*'):
                        note_lines.append(line.strip())
                    elif line.strip() and not line.strip().startswith('*') and note_lines:
                        break  # Stop at first non-note line after finding notes
                
                if note_lines:
                    storage_data[f'{table_name}_note'] = ' '.join(note_lines)
        
        return storage_data
    
    def process_single_tar(self, tar_path: str) -> List[Dict[str, Any]]:
        """
        Process a single tar.gz file
        
        Args:
            tar_path: Path to tar.gz file
            
        Returns:
            List of parsed data dictionaries
        """
        results = []
        
        # Set current tar for tracking
        self._current_tar = os.path.basename(tar_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Processing: {tar_path}")
            
            # Extract autosupport files
            autosupport_files = self.extract_tar_gz(tar_path, temp_dir)
            
            if not autosupport_files:
                print(f"  No autosupport files found in {tar_path}")
                return results
            
            # Parse each autosupport file
            for autosupport_file in autosupport_files:
                print(f"  Parsing: {os.path.basename(autosupport_file)}")
                data = self.parse_autosupport_file(autosupport_file)
                results.append(data)
        
        return results
    
    def process_single_eml(self, eml_path: str) -> List[Dict[str, Any]]:
        """
        Process a single .eml file
        
        Args:
            eml_path: Path to .eml file
            
        Returns:
            List of parsed data dictionaries
        """
        results = []
        
        # Set current source for tracking
        self._current_tar = os.path.basename(eml_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Processing: {eml_path}")
            
            # Extract autosupport content from email
            autosupport_files = self.extract_autosupport_from_eml(eml_path, temp_dir)
            
            if not autosupport_files:
                print(f"  No autosupport data found in {eml_path}")
                return results
            
            # Parse each autosupport file
            for autosupport_file in autosupport_files:
                print(f"  Parsing: {os.path.basename(autosupport_file)}")
                data = self.parse_autosupport_file(autosupport_file)
                results.append(data)
        
        return results
    
    def process_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        Process all tar.gz and .eml files in a directory
        
        Args:
            directory: Path to directory containing tar.gz and/or .eml files
            
        Returns:
            List of all parsed data dictionaries
        """
        results = []
        
        # Find all tar.gz and .eml files
        tar_files = []
        eml_files = []
        for file in os.listdir(directory):
            if file.endswith('.tar.gz'):
                tar_files.append(os.path.join(directory, file))
            elif file.endswith('.eml'):
                eml_files.append(os.path.join(directory, file))
        
        total_files = len(tar_files) + len(eml_files)
        if not total_files:
            print(f"No .tar.gz or .eml files found in {directory}")
            return results
        
        if tar_files:
            print(f"Found {len(tar_files)} tar.gz files to process")
        if eml_files:
            print(f"Found {len(eml_files)} .eml files to process")
        
        # Process each tar file
        for tar_file in sorted(tar_files):
            file_results = self.process_single_tar(tar_file)
            results.extend(file_results)
        
        # Process each eml file
        for eml_file in sorted(eml_files):
            file_results = self.process_single_eml(eml_file)
            results.extend(file_results)
        
        return results
    
    def output_to_console(self, data: List[Dict[str, Any]]) -> None:
        """
        Display parsed data in console format
        
        Args:
            data: List of parsed data dictionaries
        """
        if not data:
            print("No data to display")
            return
        
        print("\n" + "="*80)
        print("AUTOSUPPORT PARSING RESULTS")
        print("="*80)
        
        for i, entry in enumerate(data, 1):
            print(f"\n--- Entry {i} ---")
            for field in self.REQUIRED_FIELDS:
                print(f"{field:20}: {entry.get(field, 'N/A')}")
            
            # Add spacing and Services section
            print()
            print(f"{'SERVICES':20}:")
            for service in self.SERVICES:
                print(f"  {service:18}: {entry.get(service, 'Unknown')}")
            
            # Add spacing and Storage Tables section
            storage_tables = entry.get('STORAGE_TABLES', {})
            if storage_tables:
                print()
                print()
                print("STORAGE USAGE:")
                
                # Storage usage tables
                usage_tables = ['Active Tier Usage', 'Cloud Tier Usage', 'Total Usage']
                for table_name in usage_tables:
                    if table_name in storage_tables:
                        print()
                        print(f"{table_name.replace(' Usage', '')}:")
                        rows = storage_tables[table_name]
                        
                        if rows:
                            # Define clean column names and order for usage tables
                            columns = ['Resource', 'Size_GiB', 'Used_GiB', 'Avail_GiB', 'Use_Percent', 'Cleanable_GiB']
                            clean_headers = ['Resource', 'Size GiB', 'Used GiB', 'Avail GiB', 'Use%', 'Cleanable GiB']
                            
                            # Print header
                            header_line = "  " + "  ".join(f"{header:>15}" for header in clean_headers)
                            print(header_line)
                            
                            # Print rows
                            for row in rows:
                                values = []
                                for col in columns:
                                    value = row.get(col, 'N/A')
                                    # Convert '-' to 'N/A' and handle empty values
                                    if value == '-' or value == '':
                                        value = 'N/A'
                                    values.append(value)
                                
                                row_line = "  " + "  ".join(f"{str(val):>15}" for val in values)
                                print(row_line)
                        
                        # Print note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            print(f"  {storage_tables[note_key]}")
                
                # Compression statistics tables
                compression_tables = ['Active Tier Compression', 'Cloud Tier Compression', 'Currently Used Summary']
                for table_name in compression_tables:
                    if table_name in storage_tables:
                        print()
                        print()
                        print(f"{table_name.replace(' Compression', ' Compression Stats').replace(' Summary', ' Summary')}:")
                        rows = storage_tables[table_name]
                        
                        if rows:
                            # Define clean column names and order for compression tables
                            comp_columns = ['Metric', 'Pre_Comp_GiB', 'Post_Comp_GiB', 'Global_Comp_Factor', 'Local_Comp_Factor', 'Total_Comp_Factor']
                            comp_headers = ['Metric', 'Pre-Comp GiB', 'Post-Comp GiB', 'Global-Comp', 'Local-Comp', 'Total-Comp']
                            
                            # Print header
                            header_line = "  " + "  ".join(f"{header:>15}" for header in comp_headers)
                            print(header_line)
                            
                            # Print rows
                            for row in rows:
                                values = []
                                for col in comp_columns:
                                    value = row.get(col, 'N/A')
                                    # Convert '-' to 'N/A' and handle empty values
                                    if value == '-' or value == '':
                                        value = 'N/A'
                                    values.append(value)
                                
                                row_line = "  " + "  ".join(f"{str(val):>15}" for val in values)
                                print(row_line)
                        
                        # Print note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            print(f"  {storage_tables[note_key]}")
                
                # Mtree compression statistics tables
                mtree_tables = ['Mtree List', 'Mtree Active Tier Compression', 'Mtree Cloud Tier Compression']
                for table_name in mtree_tables:
                    if table_name in storage_tables:
                        print()
                        print()
                        print(f"{table_name}:")
                        rows = storage_tables[table_name]
                        
                        if rows:
                            # Handle different mtree table types
                            if table_name == 'Mtree List':
                                # Mtree List has different columns with retention lock and replication info
                                list_columns = ['Name', 'Pre_Comp_GiB', 'Status', 'Retention_Lock', 'Lock_Mode', 'Min_Retention_Period', 'Max_Retention_Period', 'Replication_Mode', 'Replication_Host', 'Replication_Enabled']
                                list_headers = ['Mtree Name', 'Pre-Comp GiB', 'Status', 'Ret Lock', 'Lock Mode', 'Min Period', 'Max Period', 'Repl Mode', 'Repl Host', 'Enabled']
                                
                                # Print header
                                header_line = f"  {list_headers[0]:<30} {list_headers[1]:>12} {list_headers[2]:<18} {list_headers[3]:<9} {list_headers[4]:<10} {list_headers[5]:<10} {list_headers[6]:<10} {list_headers[7]:<11} {list_headers[8]:<12} {list_headers[9]:<7}"
                                print(header_line)
                                
                                # Print rows
                                for i, row in enumerate(rows[:20]):  # Show more for list since it's simpler
                                    name = row.get('Name', 'N/A')
                                    size = row.get('Pre_Comp_GiB', 'N/A')
                                    status = row.get('Status', 'N/A')
                                    ret_lock = row.get('Retention_Lock', 'N/A')
                                    lock_mode = row.get('Lock_Mode', 'N/A')
                                    min_period = row.get('Min_Retention_Period', 'N/A')
                                    max_period = row.get('Max_Retention_Period', 'N/A')
                                    repl_mode = row.get('Replication_Mode', 'N/A')
                                    repl_host = row.get('Replication_Host', 'N/A')
                                    repl_enabled = row.get('Replication_Enabled', 'N/A')
                                    
                                    # Truncate long values to fit columns
                                    status = status[:17] if len(status) > 17 else status
                                    lock_mode = lock_mode[:9] if len(lock_mode) > 9 else lock_mode
                                    min_period = min_period[:9] if len(min_period) > 9 else min_period
                                    max_period = max_period[:9] if len(max_period) > 9 else max_period
                                    repl_mode = repl_mode[:10] if len(repl_mode) > 10 else repl_mode
                                    repl_host = repl_host[:11] if len(repl_host) > 11 else repl_host
                                    repl_enabled = repl_enabled[:6] if len(repl_enabled) > 6 else repl_enabled
                                    
                                    row_line = f"  {name:<30} {size:>12} {status:<18} {ret_lock:<9} {lock_mode:<10} {min_period:<10} {max_period:<10} {repl_mode:<11} {repl_host:<12} {repl_enabled:<7}"
                                    print(row_line)
                                
                                if len(rows) > 20:
                                    print(f"  ... and {len(rows) - 20} more mtrees")
                            
                            else:
                                # Define clean column names and order for mtree compression tables with separated reduction percentages
                                mtree_columns = ['Mtree', 'Pre_24hrs_GiB', 'Post_24hrs_GiB', 'Global_24hrs', 'Local_24hrs', 'Total_24hrs', 'Reduction_24hrs_Percent',
                                               'Pre_7days_GiB', 'Post_7days_GiB', 'Global_7days', 'Local_7days', 'Total_7days', 'Reduction_7days_Percent']
                                mtree_headers = ['Mtree', 'Pre-24h GiB', 'Post-24h GiB', 'Glob-24h', 'Loc-24h', 'Tot-24h', 'Red-24h%',
                                               'Pre-7d GiB', 'Post-7d GiB', 'Glob-7d', 'Loc-7d', 'Tot-7d', 'Red-7d%']
                                
                                # Print header
                                header_line = "  " + "  ".join(f"{header:>12}" for header in mtree_headers)
                                print(header_line)
                                
                                # Print rows (limit to first 10 to avoid excessive output)
                                for i, row in enumerate(rows[:10]):
                                    values = []
                                    for col in mtree_columns:
                                        value = row.get(col, 'N/A')
                                        # Convert '-' to 'N/A' and handle empty values
                                        if value == '-' or value == '':
                                            value = 'N/A'
                                        # Truncate long mtree names
                                        if col == 'Mtree' and len(str(value)) > 12:
                                            value = str(value)[:12]
                                        values.append(value)
                                    
                                    row_line = "  " + "  ".join(f"{str(val):>12}" for val in values)
                                    print(row_line)
                                
                                if len(rows) > 10:
                                    print(f"  ... and {len(rows) - 10} more mtrees")
                        
                        # Print note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            print(f"  {storage_tables[note_key]}")
            
            # Cloud Tier section (only if Cloud Tier is enabled)
            if entry.get('CLOUD_TIER') == 'Enabled':
                cloud_profiles = entry.get('CLOUD_PROFILES', [])
                cloud_movement = entry.get('CLOUD_DATA_MOVEMENT', [])
                
                if cloud_profiles or cloud_movement:
                    print()
                    print()
                    print("CLOUD TIER:")
                    print()
                    
                    # Cloud Profiles
                    if cloud_profiles:
                        print("Cloud Profiles:")
                        print(f"  {'Profile Name':<30} {'Provider':<10} {'Endpoint':<35} {'Version':<15} {'Proxy Host':<15} {'Port':<6} {'Username':<10}")
                        for profile in cloud_profiles:
                            name = profile.get('Profile_Name', 'N/A')
                            provider = profile.get('Provider', 'N/A')
                            endpoint = profile.get('Endpoint', 'N/A')
                            version = profile.get('Version', 'N/A')
                            proxy_host = profile.get('Proxy_Host', 'N/A')
                            proxy_port = profile.get('Proxy_Port', 'N/A')
                            proxy_username = profile.get('Proxy_Username', 'N/A')
                            
                            # Truncate long values for display
                            name = name[:29] if len(name) > 29 else name
                            endpoint = endpoint[:34] if len(endpoint) > 34 else endpoint
                            version = version[:14] if len(version) > 14 else version
                            proxy_host = proxy_host[:14] if len(proxy_host) > 14 else proxy_host
                            proxy_username = proxy_username[:9] if len(proxy_username) > 9 else proxy_username
                            
                            print(f"  {name:<30} {provider:<10} {endpoint:<35} {version:<15} {proxy_host:<15} {proxy_port:<6} {proxy_username:<10}")
                        print()
                    
                    # Cloud Data-Movement Configuration
                    if cloud_movement:
                        print("Cloud Data-Movement Configuration:")
                        print(f"  {'Mtree':<30} {'Target':<26} {'Policy':<15} {'Value':<15}")
                        for movement in cloud_movement:
                            mtree = movement.get('Mtree', 'N/A')
                            target = movement.get('Target', 'N/A')
                            policy = movement.get('Policy', 'N/A')
                            value = movement.get('Value', 'N/A')
                            # Truncate long values for display
                            mtree = mtree[:29] if len(mtree) > 29 else mtree
                            target = target[:25] if len(target) > 25 else target
                            print(f"  {mtree:<30} {target:<26} {policy:<15} {value:<15}")
            
            print()
            print(f"{'SOURCE_FILE':20}: {entry.get('SOURCE_FILE', 'N/A')}")
            print(f"{'SOURCE_TAR':20}: {entry.get('SOURCE_TAR', 'N/A')}")
    
    def output_to_csv(self, data: List[Dict[str, Any]], output_dir: Optional[str] = None) -> List[str]:
        """
        Generate CSV files for parsed data organized by location
        
        Creates location-based subdirectories for better organization:
        - Each autosupport's LOCATION field determines the subdirectory
        - Files are grouped by hostname within each location
        - Unknown/missing locations use 'unknown_location' folder
        - Location names are sanitized for filesystem compatibility
        
        Args:
            data: List of parsed data dictionaries
            output_dir: Directory to save CSV files (default: current directory)
            
        Returns:
            List of generated CSV file paths
            
        Example structure:
            output_dir/
            ├── DFW/
            │   ├── dedfwdp1081_data.csv
            │   └── dedfwdp1082_data.csv
            ├── NYC/
            │   └── dednydp2001_data.csv
            └── unknown_location/
                └── unknown_host_data.csv
        """
        if not data:
            print("No data to export to CSV")
            return []
        
        if output_dir is None:
            output_dir = os.getcwd()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Group data by location first, then by file identifier within each location
        location_groups = {}
        for entry in data:
            location = entry.get('LOCATION', 'unknown')
            location_folder = self.get_location_folder(location)
            hostname = entry.get('HOSTNAME', 'unknown')
            generated_on = entry.get('GENERATED_ON', 'unknown')
            source_tar = entry.get('SOURCE_TAR', 'unknown')
            file_identifier = self.get_file_identifier(hostname, generated_on, source_tar)
            
            if location_folder not in location_groups:
                location_groups[location_folder] = {}
            
            if file_identifier not in location_groups[location_folder]:
                location_groups[location_folder][file_identifier] = []
            
            location_groups[location_folder][file_identifier].append(entry)
        
        generated_files = []
        
        # Create location subdirectories and CSV files
        for location_folder, identifier_groups in location_groups.items():
            # Create location subdirectory
            location_output_dir = os.path.join(output_dir, location_folder)
            os.makedirs(location_output_dir, exist_ok=True)
            
            # Create CSV file for each file identifier group within this location
            for file_identifier, entries in identifier_groups.items():
                csv_filename = f"{file_identifier}.csv"
                csv_path = os.path.join(location_output_dir, csv_filename)
                
                try:
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        # Write header row
                        writer.writerow(['Field', 'Value'])
                        
                        # For each entry, write fields vertically (one field per row)
                        for i, entry in enumerate(entries):
                            if i > 0:  # Add separator between multiple entries
                                writer.writerow(['---', '---'])
                            
                            # Write basic fields
                            for field in self.REQUIRED_FIELDS:
                                writer.writerow([field, entry.get(field, 'N/A')])
                            
                            # Add spacing and Services section
                            writer.writerow(['', ''])  # Empty row for spacing
                            writer.writerow(['SERVICES', ''])
                            for service in self.SERVICES:
                                writer.writerow([service, entry.get(service, 'Unknown')])
                            
                            # Add spacing and Storage Tables section
                            storage_tables = entry.get('STORAGE_TABLES', {})
                            if storage_tables:
                                writer.writerow(['', ''])  # Empty row for spacing
                                writer.writerow(['', ''])  # Extra spacing
                                writer.writerow(['STORAGE USAGE', ''])
                                
                                # Storage usage tables
                                usage_tables = ['Active Tier Usage', 'Cloud Tier Usage', 'Total Usage']
                                for table_name in usage_tables:
                                    if table_name in storage_tables:
                                        writer.writerow(['', ''])  # Empty row for spacing
                                        writer.writerow([table_name.replace(' Usage', ''), ''])
                                        
                                        rows = storage_tables[table_name]
                                        if rows:
                                            # Write table header for usage tables
                                            headers = ['Resource', 'Size GiB', 'Used GiB', 'Avail GiB', 'Use%', 'Cleanable GiB']
                                            writer.writerow(headers)
                                            
                                            # Write table data rows
                                            for row in rows:
                                                row_data = [
                                                    row.get('Resource', 'N/A'),
                                                    row.get('Size_GiB', 'N/A'),
                                                    row.get('Used_GiB', 'N/A'), 
                                                    row.get('Avail_GiB', 'N/A'),
                                                    row.get('Use_Percent', 'N/A'),
                                                    row.get('Cleanable_GiB', 'N/A')
                                                ]
                                                # Convert '-' to 'N/A'
                                                row_data = ['N/A' if val == '-' else val for val in row_data]
                                                writer.writerow(row_data)
                                        
                                        # Write note if available
                                        note_key = f'{table_name}_note'
                                        if note_key in storage_tables:
                                            writer.writerow(['Note:', storage_tables[note_key]])
                                
                                # Compression statistics tables
                                compression_tables = ['Active Tier Compression', 'Cloud Tier Compression', 'Currently Used Summary']
                                for table_name in compression_tables:
                                    if table_name in storage_tables:
                                        writer.writerow(['', ''])  # Empty row for spacing
                                        writer.writerow(['', ''])  # Extra spacing
                                        writer.writerow([table_name.replace(' Compression', ' Compression Stats').replace(' Summary', ' Summary'), ''])
                                        
                                        rows = storage_tables[table_name]
                                        if rows:
                                            # Write table header for compression tables
                                            comp_headers = ['Metric', 'Pre-Comp GiB', 'Post-Comp GiB', 'Global-Comp Factor', 'Local-Comp Factor', 'Total-Comp Factor']
                                            writer.writerow(comp_headers)
                                            
                                            # Write table data rows
                                            for row in rows:
                                                row_data = [
                                                    row.get('Metric', 'N/A'),
                                                    row.get('Pre_Comp_GiB', 'N/A'),
                                                    row.get('Post_Comp_GiB', 'N/A'), 
                                                    row.get('Global_Comp_Factor', 'N/A'),
                                                    row.get('Local_Comp_Factor', 'N/A'),
                                                    row.get('Total_Comp_Factor', 'N/A')
                                                ]
                                                # Convert '-' to 'N/A'
                                                row_data = ['N/A' if val == '-' else val for val in row_data]
                                                writer.writerow(row_data)
                                        
                                        # Write note if available
                                        note_key = f'{table_name}_note'
                                        if note_key in storage_tables:
                                            writer.writerow(['Note:', storage_tables[note_key]])
                                
                                # Mtree compression statistics tables  
                                mtree_tables = ['Mtree List', 'Mtree Active Tier Compression', 'Mtree Cloud Tier Compression']
                                for table_name in mtree_tables:
                                    if table_name in storage_tables:
                                        writer.writerow(['', ''])  # Empty row for spacing
                                        writer.writerow(['', ''])  # Extra spacing
                                        writer.writerow([table_name, ''])
                                        
                                        rows = storage_tables[table_name]
                                        if rows:
                                            # Handle different mtree table types
                                            if table_name == 'Mtree List':
                                                # Write table header for mtree list with retention lock and replication info
                                                list_headers = ['Name', 'Pre-Comp GiB', 'Status', 'Retention Lock', 'Lock Mode', 'Min Retention Period', 'Max Retention Period', 'Replication Mode', 'Replication Host', 'Replication Enabled']
                                                writer.writerow(list_headers)
                                                
                                                # Write table data rows
                                                for row in rows:
                                                    row_data = [
                                                        row.get('Name', 'N/A'),
                                                        row.get('Pre_Comp_GiB', 'N/A'),
                                                        row.get('Status', 'N/A'),
                                                        row.get('Retention_Lock', 'N/A'),
                                                        row.get('Lock_Mode', 'N/A'),
                                                        row.get('Min_Retention_Period', 'N/A'),
                                                        row.get('Max_Retention_Period', 'N/A'),
                                                        row.get('Replication_Mode', 'N/A'),
                                                        row.get('Replication_Host', 'N/A'),
                                                        row.get('Replication_Enabled', 'N/A')
                                                    ]
                                                    writer.writerow(row_data)
                                            else:
                                                # Write table header for mtree compression tables with separated reduction percentages
                                                mtree_headers = ['Mtree', 'Pre-24hrs GiB', 'Post-24hrs GiB', 'Global-24hrs', 'Local-24hrs', 'Total-24hrs', 'Reduction-24hrs %',
                                                               'Pre-7days GiB', 'Post-7days GiB', 'Global-7days', 'Local-7days', 'Total-7days', 'Reduction-7days %']
                                                writer.writerow(mtree_headers)
                                                
                                                # Write table data rows
                                                for row in rows:
                                                    row_data = [
                                                        row.get('Mtree', 'N/A'),
                                                        row.get('Pre_24hrs_GiB', 'N/A'),
                                                        row.get('Post_24hrs_GiB', 'N/A'),
                                                        row.get('Global_24hrs', 'N/A'),
                                                        row.get('Local_24hrs', 'N/A'),
                                                        row.get('Total_24hrs', 'N/A'),
                                                        row.get('Reduction_24hrs_Percent', 'N/A'),
                                                        row.get('Pre_7days_GiB', 'N/A'),
                                                        row.get('Post_7days_GiB', 'N/A'),
                                                        row.get('Global_7days', 'N/A'),
                                                        row.get('Local_7days', 'N/A'),
                                                        row.get('Total_7days', 'N/A'),
                                                        row.get('Reduction_7days_Percent', 'N/A')
                                                    ]
                                                    # Convert '-' to 'N/A'
                                                    row_data = ['N/A' if val == '-' else val for val in row_data]
                                                    writer.writerow(row_data)
                                        
                                        # Write note if available
                                        note_key = f'{table_name}_note'
                                        if note_key in storage_tables:
                                            writer.writerow(['Note:', storage_tables[note_key]])
                            
                            # Cloud Tier section (only if Cloud Tier is enabled)
                            if entry.get('CLOUD_TIER') == 'Enabled':
                                cloud_profiles = entry.get('CLOUD_PROFILES', [])
                                cloud_movement = entry.get('CLOUD_DATA_MOVEMENT', [])
                                
                                if cloud_profiles or cloud_movement:
                                    writer.writerow(['', ''])  # Empty row for spacing
                                    writer.writerow(['CLOUD TIER', ''])
                                    writer.writerow(['', ''])  # Empty row for spacing
                                    
                                    # Cloud Profiles
                                    if cloud_profiles:
                                        writer.writerow(['Cloud Profiles', ''])
                                        writer.writerow(['Profile Name', 'Provider', 'Endpoint', 'Version', 'Proxy Host', 'Proxy Port', 'Proxy Username'])
                                        for profile in cloud_profiles:
                                            writer.writerow([
                                                profile.get('Profile_Name', 'N/A'),
                                                profile.get('Provider', 'N/A'),
                                                profile.get('Endpoint', 'N/A'),
                                                profile.get('Version', 'N/A'),
                                                profile.get('Proxy_Host', 'N/A'),
                                                profile.get('Proxy_Port', 'N/A'),
                                                profile.get('Proxy_Username', 'N/A')
                                            ])
                                        writer.writerow(['', ''])  # Empty row for spacing
                                    
                                    # Cloud Data-Movement Configuration
                                    if cloud_movement:
                                        writer.writerow(['Cloud Data-Movement Configuration', ''])
                                        writer.writerow(['Mtree', 'Target', 'Policy', 'Value'])
                                        for movement in cloud_movement:
                                            writer.writerow([
                                                movement.get('Mtree', 'N/A'),
                                                movement.get('Target', 'N/A'),
                                                movement.get('Policy', 'N/A'),
                                                movement.get('Value', 'N/A')
                                            ])
                            
                            # Add spacing and source info
                            writer.writerow(['', ''])  # Empty row for spacing
                            writer.writerow(['SOURCE_FILE', entry.get('SOURCE_FILE', 'N/A')])
                            writer.writerow(['SOURCE_TAR', entry.get('SOURCE_TAR', 'N/A')])
                    
                    generated_files.append(csv_path)
                    print(f"Generated CSV: {csv_path} ({len(entries)} entries)")
                    
                except Exception as e:
                    print(f"Error creating CSV {csv_path}: {e}")
        
        # Print location summary
        if generated_files:
            print(f"\nLocation-based organization summary:")
            location_summary = {}
            for file_path in generated_files:
                # Extract location from path structure
                path_parts = file_path.split(os.sep)
                if len(path_parts) >= 2:
                    location = path_parts[-2]  # Second to last part is location folder
                    if location not in location_summary:
                        location_summary[location] = []
                    location_summary[location].append(os.path.basename(file_path))
            
            for location, files in location_summary.items():
                print(f"  📁 {location}/ ({len(files)} files)")
                for file in files:
                    print(f"    📄 {file}")
        
        return generated_files
    
    def output_to_html(self, data: List[Dict[str, Any]], output_dir: Optional[str] = None) -> List[str]:
        """
        Generate HTML files for parsed data organized by location
        
        Creates location-based subdirectories with nicely formatted HTML tables:
        - Each autosupport's LOCATION field determines the subdirectory
        - Files are grouped by hostname within each location
        - Tables have centered column headers, left-justified row labels, right-justified data
        - Responsive design with proper styling
        
        Args:
            data: List of parsed data dictionaries
            output_dir: Directory to save HTML files (default: current directory)
            
        Returns:
            List of generated HTML file paths
        """
        if not data:
            print("No data to export to HTML")
            return []
        
        if output_dir is None:
            output_dir = os.getcwd()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Group data by location first, then by file identifier within each location
        location_groups = {}
        for entry in data:
            location = entry.get('LOCATION', 'unknown')
            location_folder = self.get_location_folder(location)
            hostname = entry.get('HOSTNAME', 'unknown')
            generated_on = entry.get('GENERATED_ON', 'unknown')
            source_tar = entry.get('SOURCE_TAR', 'unknown')
            file_identifier = self.get_file_identifier(hostname, generated_on, source_tar)
            
            if location_folder not in location_groups:
                location_groups[location_folder] = {}
            
            if file_identifier not in location_groups[location_folder]:
                location_groups[location_folder][file_identifier] = []
            
            location_groups[location_folder][file_identifier].append(entry)
        
        generated_files = []
        
        # Create location subdirectories and HTML files
        for location_folder, identifier_groups in location_groups.items():
            # Create location subdirectory
            location_output_dir = os.path.join(output_dir, location_folder)
            os.makedirs(location_output_dir, exist_ok=True)
            
            # Create HTML file for each file identifier group within this location
            for file_identifier, entries in identifier_groups.items():
                html_filename = f"{file_identifier}.html"
                html_path = os.path.join(location_output_dir, html_filename)
                
                try:
                    with open(html_path, 'w', encoding='utf-8') as htmlfile:
                        # Write HTML content (use first entry's hostname for title)
                        hostname_prefix = self.get_hostname_prefix(entries[0].get('HOSTNAME', 'unknown'))
                        htmlfile.write(self._generate_html_content(entries, hostname_prefix))
                    
                    generated_files.append(html_path)
                    print(f"Generated HTML: {html_path} ({len(entries)} entries)")
                    
                except Exception as e:
                    print(f"Error creating HTML {html_path}: {e}")
        
        # Print location summary
        if generated_files:
            print(f"\nLocation-based organization summary:")
            location_summary = {}
            for file_path in generated_files:
                # Extract location from path structure
                path_parts = file_path.split(os.sep)
                if len(path_parts) >= 2:
                    location = path_parts[-2]  # Second to last part is location folder
                    if location not in location_summary:
                        location_summary[location] = []
                    location_summary[location].append(os.path.basename(file_path))
            
            for location, files in location_summary.items():
                print(f"  📁 {location}/ ({len(files)} files)")
                for file in files:
                    print(f"    📄 {file}")
        
        return generated_files
    
    def _generate_html_content(self, entries: List[Dict[str, Any]], hostname_prefix: str) -> str:
        """
        Generate HTML content for autosupport entries
        
        Args:
            entries: List of autosupport data entries
            hostname_prefix: Hostname prefix for the title
            
        Returns:
            Complete HTML content as string
        """
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{hostname_prefix} - Data Domain Autosupport Report</title>
    <style>
        /* Cohesity official green palette */
        :root {{
            --brand-green: #00DD68; /* official Cohesity green */
            --brand-green-dark: #00b355;
            --surface: #ffffff;
            --muted: #e6eef0;
            --text: #0f172a;
            --subtle: #475569;
        }}
        body {{
            font-family: 'Inter', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f7faf8 0%, #eef6f1 100%);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: var(--surface);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.06);
            border: 1px solid var(--muted);
        }}
        h1 {{
            color: var(--text);
            text-align: center;
            font-size: 2.25rem;
            font-weight: 700;
            margin-bottom: 40px;
            position: relative;
            padding-bottom: 20px;
        }}
        /* make the first letter of the host name the green accent to mimic the brand mark */
        h1 .host::first-letter {{
            color: var(--brand-green);
            font-weight: 800;
        }}
        h1::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 4px;
            background: linear-gradient(90deg, var(--brand-green) 0%, var(--brand-green-dark) 100%);
            border-radius: 2px;
        }}
        h2 {{
            color: var(--text);
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 40px;
            margin-bottom: 20px;
            padding: 12px 20px;
            background: linear-gradient(90deg, #f6fbf8 0%, #eef6f1 100%);
            border-left: 5px solid var(--brand-green);
            border-radius: 0 8px 8px 0;
        }}
        h3 {{
            color: #334155;
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #eef6f1;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            background-color: var(--surface);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            border: 1px solid var(--muted);
        }}
        th {{
            background: var(--brand-green);
            color: #ffffff;
            padding: 16px 12px;
            text-align: center;
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: none;
        }}
        td.label {{
            background-color: #fbfdfb;
            font-weight: 600;
            text-align: left;
            padding: 14px 16px;
            border: 1px solid var(--muted);
            color: var(--subtle);
            width: 220px;
        }}
        td.value {{
            text-align: right;
            padding: 14px 16px;
            border: 1px solid var(--muted);
            color: var(--text);
            font-weight: 500;
        }}
        tr:nth-child(even) {{
            background-color: #f6fbf8;
        }}
        tr:hover {{
            background-color: #e8f9ee;
            transform: translateY(-1px);
            transition: all 0.2s ease;
        }}
        .entry-separator {{
            margin: 50px 0;
            border-top: 3px solid var(--brand-green);
            padding-top: 30px;
            position: relative;
        }}
        .entry-separator::before {{
            content: '';
            position: absolute;
            top: -2px;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, var(--brand-green) 50%, transparent 100%);
        }}
        .note {{
            background: linear-gradient(135deg, #f0fff4 0%, #dcffe8 100%);
            border: 1px solid #7dd48b;
            border-radius: 8px;
            padding: 16px 20px;
            margin: 20px 0;
            font-style: italic;
            color: #04512b;
            position: relative;
            box-shadow: 0 2px 8px rgba(34,197,94,0.06);
        }}
        .note::before {{
            content: '💡';
            position: absolute;
            left: -8px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--brand-green);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }}
        .section-header {{
            background: linear-gradient(135deg, #0f172a 0%, #071017 100%);
            color: #ffffff;
            text-align: center;
            padding: 16px;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1><span class="host">{hostname_prefix}</span> <span class="separator">—</span> <span class="title-text">Data Domain Autosupport Report</span></h1>
"""
        
        # Process each entry
        for i, entry in enumerate(entries):
            if i > 0:
                html_content += '<div class="entry-separator"></div>'
            
            # Removed automatic 'Entry N' heading to keep header focused on hostname
            
            # Basic system information
            html_content += '<h3>System Information</h3>'
            html_content += '<table>'
            for field in self.REQUIRED_FIELDS:
                value = entry.get(field, 'N/A')
                html_content += f'<tr><td class="label">{field}</td><td class="value">{value}</td></tr>'
            html_content += '</table>'
            
            # Services status
            html_content += '<h3>Services Status</h3>'
            html_content += '<table>'
            for service in self.SERVICES:
                status = entry.get(service, 'Unknown')
                html_content += f'<tr><td class="label">{service}</td><td class="value">{status}</td></tr>'
            html_content += '</table>'
            
            # Storage tables
            storage_tables = entry.get('STORAGE_TABLES', {})
            if storage_tables:
                html_content += '<div class="section-header">STORAGE USAGE</div>'
                
                # Storage usage tables
                usage_tables = ['Active Tier Usage', 'Cloud Tier Usage', 'Total Usage']
                for table_name in usage_tables:
                    if table_name in storage_tables:
                        html_content += f'<h3>{table_name.replace(" Usage", "")}</h3>'
                        rows = storage_tables[table_name]
                        if rows:
                            html_content += '<table>'
                            html_content += '<tr><th>Resource</th><th>Size GiB</th><th>Used GiB</th><th>Avail GiB</th><th>Use%</th><th>Cleanable GiB</th></tr>'
                            for row in rows:
                                html_content += '<tr>'
                                html_content += f'<td class="label">{row.get("Resource", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Size_GiB", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Used_GiB", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Avail_GiB", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Use_Percent", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Cleanable_GiB", "N/A")}</td>'
                                html_content += '</tr>'
                            html_content += '</table>'
                        
                        # Add note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            html_content += f'<div class="note">{storage_tables[note_key]}</div>'
                
                # Compression statistics tables
                compression_tables = ['Active Tier Compression', 'Cloud Tier Compression', 'Currently Used Summary']
                for table_name in compression_tables:
                    if table_name in storage_tables:
                        html_content += f'<h3>{table_name.replace(" Compression", " Compression Stats").replace(" Summary", " Summary")}</h3>'
                        rows = storage_tables[table_name]
                        if rows:
                            html_content += '<table>'
                            html_content += '<tr><th>Metric</th><th>Pre-Comp GiB</th><th>Post-Comp GiB</th><th>Global-Comp Factor</th><th>Local-Comp Factor</th><th>Total-Comp Factor</th></tr>'
                            for row in rows:
                                html_content += '<tr>'
                                html_content += f'<td class="label">{row.get("Metric", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Pre_Comp_GiB", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Post_Comp_GiB", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Global_Comp_Factor", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Local_Comp_Factor", "N/A")}</td>'
                                html_content += f'<td class="value">{row.get("Total_Comp_Factor", "N/A")}</td>'
                                html_content += '</tr>'
                            html_content += '</table>'
                        
                        # Add note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            html_content += f'<div class="note">{storage_tables[note_key]}</div>'
                
                # Mtree tables
                mtree_tables = ['Mtree List', 'Mtree Active Tier Compression', 'Mtree Cloud Tier Compression']
                for table_name in mtree_tables:
                    if table_name in storage_tables:
                        html_content += f'<h3>{table_name}</h3>'
                        rows = storage_tables[table_name]
                        if rows:
                            html_content += '<table>'
                            
                            if table_name == 'Mtree List':
                                # Mtree List headers
                                html_content += '<tr><th>Name</th><th>Pre-Comp GiB</th><th>Status</th><th>Ret Lock</th><th>Lock Mode</th><th>Min Period</th><th>Max Period</th><th>Repl Mode</th><th>Repl Host</th><th>Enabled</th></tr>'
                                for row in rows:  # Show all rows
                                    html_content += '<tr>'
                                    html_content += f'<td class="label">{row.get("Name", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Pre_Comp_GiB", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Status", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Retention_Lock", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Lock_Mode", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Min_Retention_Period", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Max_Retention_Period", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Replication_Mode", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Replication_Host", "N/A")}</td>'
                                    html_content += f'<td class="value">{row.get("Replication_Enabled", "N/A")}</td>'
                                    html_content += '</tr>'
                            else:
                                # Mtree compression headers
                                html_content += '<tr><th>Mtree</th><th>Pre-24hrs GiB</th><th>Post-24hrs GiB</th><th>Global-24hrs</th><th>Local-24hrs</th><th>Total-24hrs</th><th>Red-24hrs %</th><th>Pre-7days GiB</th><th>Post-7days GiB</th><th>Global-7days</th><th>Local-7days</th><th>Total-7days</th><th>Red-7days %</th></tr>'
                                for row in rows:  # Show all rows
                                    html_content += '<tr>'
                                    html_content += f'<td class="label">{row.get("Mtree", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Pre_24hrs_GiB", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Post_24hrs_GiB", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Global_24hrs", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Local_24hrs", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Total_24hrs", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Reduction_24hrs_Percent", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Pre_7days_GiB", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Post_7days_GiB", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Global_7days", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Local_7days", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Total_7days", "-").replace("N/A", "-")}</td>'
                                    html_content += f'<td class="value">{row.get("Reduction_7days_Percent", "-").replace("N/A", "-")}</td>'
                                    html_content += '</tr>'
                            
                            html_content += '</table>'
                        
                        # Add note if available
                        note_key = f'{table_name}_note'
                        if note_key in storage_tables:
                            html_content += f'<div class="note">{storage_tables[note_key]}</div>'
            
            # Cloud Tier section
            if entry.get('CLOUD_TIER') == 'Enabled':
                cloud_profiles = entry.get('CLOUD_PROFILES', [])
                cloud_movement = entry.get('CLOUD_DATA_MOVEMENT', [])
                
                if cloud_profiles or cloud_movement:
                    html_content += '<div class="section-header">CLOUD TIER</div>'
                    
                    # Cloud Profiles
                    if cloud_profiles:
                        html_content += '<h3>Cloud Profiles</h3>'
                        html_content += '<table>'
                        html_content += '<tr><th>Profile Name</th><th>Provider</th><th>Endpoint</th><th>Version</th><th>Proxy Host</th><th>Proxy Port</th><th>Proxy Username</th></tr>'
                        for profile in cloud_profiles:
                            html_content += '<tr>'
                            html_content += f'<td class="label">{profile.get("Profile_Name", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Provider", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Endpoint", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Version", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Proxy_Host", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Proxy_Port", "N/A")}</td>'
                            html_content += f'<td class="value">{profile.get("Proxy_Username", "N/A")}</td>'
                            html_content += '</tr>'
                        html_content += '</table>'
                    
                    # Cloud Data-Movement Configuration
                    if cloud_movement:
                        html_content += '<h3>Cloud Data-Movement Configuration</h3>'
                        html_content += '<table>'
                        html_content += '<tr><th>Mtree</th><th>Target</th><th>Policy</th><th>Value</th></tr>'
                        for movement in cloud_movement:
                            html_content += '<tr>'
                            html_content += f'<td class="label">{movement.get("Mtree", "N/A")}</td>'
                            html_content += f'<td class="value">{movement.get("Target", "N/A")}</td>'
                            html_content += f'<td class="value">{movement.get("Policy", "N/A")}</td>'
                            html_content += f'<td class="value">{movement.get("Value", "N/A")}</td>'
                            html_content += '</tr>'
                        html_content += '</table>'
            
            # Source information
            html_content += '<h3>Source Information</h3>'
            html_content += '<table>'
            html_content += f'<tr><td class="label">SOURCE_FILE</td><td class="value">{entry.get("SOURCE_FILE", "N/A")}</td></tr>'
            html_content += f'<tr><td class="label">SOURCE_TAR</td><td class="value">{entry.get("SOURCE_TAR", "N/A")}</td></tr>'
            html_content += '</table>'
        
        # Close HTML
        html_content += """
    </div>
</body>
</html>"""
        
        return html_content
    
    def run(self, input_path: str, output_format: str = 'console', output_dir: Optional[str] = None) -> None:
        """
        Main execution method
        
        Args:
            input_path: Path to tar.gz file or directory containing tar.gz files
            output_format: Output format ('console', 'csv', or 'html')
            output_dir: Directory for file output (if applicable)
        """
        print(f"Autosupport Parser Starting...")
        print(f"Input: {input_path}")
        print(f"Output format: {output_format}")
        
        # Determine input type and process
        if os.path.isfile(input_path):
            if input_path.endswith('.tar.gz'):
                # Single tar.gz file
                self.parsed_data = self.process_single_tar(input_path)
            elif input_path.endswith('.eml'):
                # Single .eml file
                self.parsed_data = self.process_single_eml(input_path)
            else:
                print(f"Error: {input_path} is not a valid .tar.gz or .eml file")
                return
        elif os.path.isdir(input_path):
            # Directory containing tar.gz and/or .eml files
            self.parsed_data = self.process_directory(input_path)
        else:
            print(f"Error: {input_path} is not a valid file or directory")
            return
        
        if not self.parsed_data:
            print("No data was parsed successfully")
            return
        
        print(f"\nSuccessfully parsed {len(self.parsed_data)} autosupport entries")
        
        # Output results based on format
        if output_format == 'console':
            self.output_to_console(self.parsed_data)
        
        elif output_format == 'csv':
            generated_files = self.output_to_csv(self.parsed_data, output_dir)
            if generated_files:
                print(f"\nGenerated {len(generated_files)} CSV files")
        
        elif output_format == 'html':
            generated_files = self.output_to_html(self.parsed_data, output_dir)
            if generated_files:
                print(f"\nGenerated {len(generated_files)} HTML files")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Extract and parse Data Domain autosupport files from tar.gz archives or .eml email files. CSV output automatically organizes files by location into subdirectories.',
        epilog='Examples: python autosupport_parser.py /path/to/file.tar.gz --format csv --output ./results\n          python autosupport_parser.py /path/to/autosupport.eml --format html'
    )
    
    parser.add_argument(
        'input_path',
        help='Path to tar.gz file, .eml file, or directory containing tar.gz and/or .eml files'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['console', 'csv', 'html'],
        default='console',
        help='Output format (default: console)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output directory for CSV files. Files are organized in location-based subdirectories (default: current directory)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Autosupport Parser 1.0'
    )
    
    args = parser.parse_args()
    
    # Validate input path
    if not os.path.exists(args.input_path):
        print(f"Error: Input path '{args.input_path}' does not exist")
        return 1
    
    # Create parser and run
    autosupport_parser = AutosupportParser()
    try:
        autosupport_parser.run(args.input_path, args.format, args.output)
        return 0
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
