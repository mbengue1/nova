#!/usr/bin/env python3
"""
Nova CLI - Management tool for Nova daemon
"""

import os
import sys
import json
import socket
import subprocess
import argparse
from typing import Dict, Any, Optional

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class NovaCLI:
    """Nova Command Line Interface"""
    
    def __init__(self):
        self.socket_path = "/tmp/nova.sock"
        self.plist_path = os.path.expanduser("~/Library/LaunchAgents/com.nova.daemon.plist")
        self.daemon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'daemon', 'novad.py'))
    
    def status(self) -> bool:
        """Check Nova daemon status"""
        print("📊 Nova Daemon Status")
        print("=" * 40)
        
        # Check if socket exists
        if os.path.exists(self.socket_path):
            print("✅ IPC Socket: Active")
            
            # Try to connect and get status
            try:
                response = self._send_ipc_message({"type": "Status"})
                if response:
                    print(f"🟢 Status: {response.get('status', 'unknown')}")
                    print(f"🔄 State: {response.get('state', 'unknown')}")
                    print(f"🔌 Clients: {response.get('clients', 0)}")
                    print(f"⚡ Workers: {response.get('workers', 0)}")
                    print(f"📡 Socket: {response.get('socket_path', 'unknown')}")
                    
                    # Show smart scheduling info
                    if 'smart_scheduling' in response:
                        scheduling = response['smart_scheduling']
                        print(f"\n🎓 Smart Scheduling:")
                        print(f"   Scheduled to run: {'✅ Yes' if scheduling.get('scheduled_to_run') else '❌ No'}")
                        print(f"   Reason: {scheduling.get('reason', 'Unknown')}")
                        print(f"   Buffer time: {scheduling.get('buffer_minutes', 0)} minutes")
                        
                        if scheduling.get('current_class'):
                            current = scheduling['current_class']
                            print(f"   Current class: {current.get('name', 'Unknown')}")
                        
                        if scheduling.get('next_class'):
                            next_class = scheduling['next_class']
                            print(f"   Next class: {next_class.get('name', 'Unknown')} at {next_class.get('start', 'Unknown')}")
                    
                    return True
                else:
                    print("⚠️ Status: Connected but no response")
                    return False
            except Exception as e:
                print(f"❌ Status: Socket error - {e}")
                return False
        else:
            print("❌ IPC Socket: Not found")
            return False
    
    def health(self) -> bool:
        """Check Nova daemon health"""
        print("🏥 Nova Daemon Health Check")
        print("=" * 40)
        
        if not os.path.exists(self.socket_path):
            print("❌ Daemon not running")
            return False
        
        try:
            response = self._send_ipc_message({"type": "Health"})
            if response:
                print(f"🟢 Status: {response.get('status', 'unknown')}")
                print(f"🔄 State: {response.get('state', 'unknown')}")
                print(f"🔌 Clients: {response.get('clients', 0)}")
                print(f"⚡ Workers: {response.get('workers', 0)}")
                print(f"⏱️ Uptime: {response.get('uptime', 0):.0f}s")
                return True
            else:
                print("❌ Health check failed")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def enable(self) -> bool:
        """Enable Nova daemon to start at login"""
        print("🔧 Enabling Nova Daemon")
        print("=" * 40)
        
        try:
            # Check if plist exists
            if not os.path.exists(self.plist_path):
                print("❌ Launch agent plist not found")
                print(f"   Expected: {self.plist_path}")
                return False
            
            # Load the launch agent
            result = subprocess.run([
                'launchctl', 'load', self.plist_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Nova daemon enabled for auto-start")
                return True
            else:
                print(f"❌ Failed to enable: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Enable failed: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable Nova daemon from starting at login"""
        print("🔧 Disabling Nova Daemon")
        print("=" * 40)
        
        try:
            # Unload the launch agent
            result = subprocess.run([
                'launchctl', 'unload', self.plist_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Nova daemon disabled from auto-start")
                return True
            else:
                print(f"❌ Failed to disable: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Disable failed: {e}")
            return False
    
    def start(self) -> bool:
        """Start Nova daemon manually"""
        print("🚀 Starting Nova Daemon")
        print("=" * 40)
        
        try:
            # Check if daemon script exists
            if not os.path.exists(self.daemon_path):
                print(f"❌ Daemon script not found: {self.daemon_path}")
                return False
            
            # Start daemon in background
            result = subprocess.run([
                'python3', self.daemon_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Nova daemon started successfully")
                return True
            else:
                print(f"❌ Failed to start: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✅ Nova daemon started (background)")
            return True
        except Exception as e:
            print(f"❌ Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop Nova daemon"""
        print("🛑 Stopping Nova Daemon")
        print("=" * 40)
        
        try:
            # Try graceful shutdown via IPC
            if os.path.exists(self.socket_path):
                try:
                    response = self._send_ipc_message({"type": "Shutdown"})
                    if response:
                        print("✅ Graceful shutdown initiated")
                        return True
                except:
                    pass
            
            # Force kill if IPC fails
            result = subprocess.run([
                'pkill', '-f', 'novad.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Nova daemon stopped")
                return True
            else:
                print("⚠️ No daemon processes found")
                return True
                
        except Exception as e:
            print(f"❌ Stop failed: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart Nova daemon"""
        print("🔄 Restarting Nova Daemon")
        print("=" * 40)
        
        if self.stop() and self.start():
            print("✅ Nova daemon restarted successfully")
            return True
        else:
            print("❌ Restart failed")
            return False
    
    def logs(self, lines: int = 50) -> bool:
        """Show Nova daemon logs"""
        print(f"📋 Nova Daemon Logs (last {lines} lines)")
        print("=" * 40)
        
        log_file = "/tmp/nova_daemon.log"
        
        if not os.path.exists(log_file):
            print("❌ Log file not found")
            return False
        
        try:
            # Read last N lines
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in last_lines:
                    print(line.rstrip())
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to read logs: {e}")
            return False
    
    def schedule(self) -> bool:
        """Show detailed scheduling information"""
        print("🎓 Nova Smart Scheduling Status")
        print("=" * 50)
        
        if not os.path.exists(self.socket_path):
            print("❌ Daemon not running - cannot check scheduling")
            return False
        
        try:
            response = self._send_ipc_message({"type": "Status"})
            if response and 'smart_scheduling' in response:
                scheduling = response['smart_scheduling']
                
                print(f"🕐 Current Status:")
                print(f"   Scheduled to run: {'✅ Yes' if scheduling.get('scheduled_to_run') else '❌ No'}")
                print(f"   Reason: {scheduling.get('reason', 'Unknown')}")
                print(f"   Buffer time: {scheduling.get('buffer_minutes', 0)} minutes")
                print(f"   Class protection: {'✅ Enabled' if scheduling.get('class_hours_protection') == 'enabled' else '❌ Disabled'}")
                
                print(f"\n📚 Current Class:")
                if scheduling.get('current_class'):
                    current = scheduling['current_class']
                    print(f"   Name: {current.get('name', 'Unknown')}")
                    print(f"   Time: {current.get('start', 'Unknown')} - {current.get('end', 'Unknown')}")
                    print(f"   Location: {current.get('location', 'Unknown')}")
                    print(f"   Instructor: {current.get('instructor', 'Unknown')}")
                else:
                    print("   None currently in session")
                
                print(f"\n⏰ Next Class:")
                if scheduling.get('next_class'):
                    next_class = scheduling['next_class']
                    print(f"   Name: {next_class.get('name', 'Unknown')}")
                    print(f"   Time: {next_class.get('start', 'Unknown')} - {next_class.get('next_class', 'Unknown')}")
                    print(f"   Location: {next_class.get('location', 'Unknown')}")
                else:
                    print("   No upcoming classes today")
                
                return True
            else:
                print("❌ Could not retrieve scheduling information")
                return False
                
        except Exception as e:
            print(f"❌ Schedule check error: {e}")
            return False
    
    def doctor(self) -> bool:
        """Run diagnostic checks"""
        print("🔍 Nova Daemon Diagnostics")
        print("=" * 40)
        
        checks = []
        
        # Check 1: Daemon script
        if os.path.exists(self.daemon_path):
            print("✅ Daemon script: Found")
            checks.append(True)
        else:
            print(f"❌ Daemon script: Not found at {self.daemon_path}")
            checks.append(False)
        
        # Check 2: Launch agent
        if os.path.exists(self.plist_path):
            print("✅ Launch agent: Found")
            checks.append(True)
        else:
            print(f"❌ Launch agent: Not found at {self.plist_path}")
            checks.append(False)
        
        # Check 3: IPC socket
        if os.path.exists(self.socket_path):
            print("✅ IPC socket: Active")
            checks.append(True)
        else:
            print("❌ IPC socket: Not found")
            checks.append(False)
        
        # Check 4: Python environment
        try:
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Python: {result.stdout.strip()}")
                checks.append(True)
            else:
                print("❌ Python: Not available")
                checks.append(False)
        except:
            print("❌ Python: Not available")
            checks.append(False)
        
        # Check 5: Dependencies
        try:
            import spotipy
            print("✅ Spotify: Available")
            checks.append(True)
        except ImportError:
            print("❌ Spotify: Not available")
            checks.append(False)
        
        # Summary
        print("\n📊 Diagnostic Summary:")
        passed = sum(checks)
        total = len(checks)
        print(f"   {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All systems operational!")
            return True
        else:
            print("⚠️ Some issues detected")
            return False
    
    def _send_ipc_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send message to Nova daemon via IPC"""
        try:
            if not os.path.exists(self.socket_path):
                return None
            
            # Create socket connection
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.socket_path)
            
            # Send message
            sock.send(json.dumps(message).encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(4096)
            sock.close()
            
            if response_data:
                return json.loads(response_data.decode('utf-8'))
            
        except Exception:
            pass
        
        return None

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Nova Daemon Management CLI")
    parser.add_argument('command', choices=[
        'status', 'health', 'enable', 'disable', 
        'start', 'stop', 'restart', 'logs', 'schedule', 'doctor'
    ], help='Command to execute')
    
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='Number of log lines to show (default: 50)')
    
    args = parser.parse_args()
    
    cli = NovaCLI()
    
    # Execute command
    if args.command == 'status':
        success = cli.status()
    elif args.command == 'health':
        success = cli.health()
    elif args.command == 'enable':
        success = cli.enable()
    elif args.command == 'disable':
        success = cli.disable()
    elif args.command == 'start':
        success = cli.start()
    elif args.command == 'stop':
        success = cli.stop()
    elif args.command == 'restart':
        success = cli.restart()
    elif args.command == 'logs':
        success = cli.logs(args.lines)
    elif args.command == 'schedule':
        success = cli.schedule()
    elif args.command == 'doctor':
        success = cli.doctor()
    else:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
