#!/usr/bin/env python3
"""
Test IPC Server for Nova Daemon
Tests daemon ↔ worker communication before full Go implementation
"""

import json
import socket
import threading
import time
import logging
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class NovaIPCServer:
    """Simple IPC server for testing daemon ↔ worker communication"""
    
    def __init__(self, socket_path: str = "/tmp/nova.sock"):
        self.socket_path = socket_path
        self.server_socket = None
        self.clients = []
        self.running = False
        self.state = "IDLE"
        self.workers = {}
        self.message_handlers = {
            "WakeDetected": self._handle_wake_detected,
            "BeginSTT": self._handle_begin_stt,
            "NLPRoute": self._handle_nlp_route,
            "ExecuteSkill": self._handle_execute_skill,
            "Speak": self._handle_speak,
            "Transition": self._handle_transition,
            "Health": self._handle_health,
            "Status": self._handle_status
        }
        
        # Clean up existing socket
        if os.path.exists(socket_path):
            os.unlink(socket_path)
    
    def start(self):
        """Start the IPC server"""
        print(f"🚀 Starting Nova IPC Server on {self.socket_path}")
        
        try:
            # Create Unix domain socket
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            
            # Set socket permissions
            os.chmod(self.socket_path, 0o600)
            
            self.running = True
            print(f"✅ IPC Server listening on {self.socket_path}")
            
            # Start accepting connections
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"🔌 New client connected")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"⚠️ Client connection error: {e}")
                        
        except Exception as e:
            print(f"❌ Failed to start IPC server: {e}")
            return False
        
        return True
    
    def stop(self):
        """Stop the IPC server"""
        print("🛑 Stopping Nova IPC Server...")
        self.running = False
        
        # Close client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Clean up socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        print("✅ IPC Server stopped")
    
    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        self.clients.append(client_socket)
        
        try:
            while self.running:
                # Receive message
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse JSON message
                try:
                    message = json.loads(data.decode('utf-8'))
                    print(f"📨 Received: {message.get('type', 'Unknown')}")
                    
                    # Handle message
                    response = self._process_message(message)
                    
                    # Send response
                    if response:
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                    error_response = {
                        "type": "Error",
                        "error": "Invalid JSON format",
                        "details": str(e)
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"⚠️ Client handling error: {e}")
        finally:
            # Clean up
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print("🔌 Client disconnected")
    
    def _process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming message and return response"""
        message_type = message.get('type')
        
        if message_type in self.message_handlers:
            return self.message_handlers[message_type](message)
        else:
            return {
                "type": "Error",
                "error": "Unknown message type",
                "details": f"Unsupported type: {message_type}"
            }
    
    def _handle_wake_detected(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle wake word detection"""
        print(f"👂 Wake word detected at {message.get('ts', 'unknown')}")
        self.state = "LISTENING"
        
        return {
            "type": "WakeDetected",
            "status": "success",
            "state": self.state,
            "timestamp": time.time()
        }
    
    def _handle_begin_stt(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle speech-to-text request"""
        req_id = message.get('req_id', 'unknown')
        max_seconds = message.get('max_seconds', 10)
        
        print(f"🎤 STT request {req_id} for {max_seconds}s")
        
        # Simulate STT processing
        time.sleep(1)  # Simulate processing time
        
        return {
            "type": "STTResult",
            "req_id": req_id,
            "text": "Hello Nova, what's my schedule for today?",
            "confidence": 0.95,
            "status": "success"
        }
    
    def _handle_nlp_route(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle NLP routing request"""
        req_id = message.get('req_id', 'unknown')
        text = message.get('text', '')
        
        print(f"🧠 NLP routing request {req_id}: '{text}'")
        
        # Simple intent detection
        if "schedule" in text.lower():
            intent = "GetSchedule"
            slots = {"timeframe": "today"}
        elif "music" in text.lower() or "spotify" in text.lower():
            intent = "ControlMusic"
            slots = {"action": "play"}
        elif "focus" in text.lower() or "dnd" in text.lower():
            intent = "ControlFocus"
            slots = {"mode": "Do Not Disturb"}
        else:
            intent = "Unknown"
            slots = {}
        
        return {
            "type": "Intent",
            "req_id": req_id,
            "intent": intent,
            "slots": slots,
            "reply_template": f"I'll help you with {intent}",
            "status": "success"
        }
    
    def _handle_execute_skill(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill execution request"""
        req_id = message.get('req_id', 'unknown')
        intent = message.get('intent', {})
        
        print(f"⚡ Skill execution request {req_id}: {intent}")
        
        # Simulate skill execution
        time.sleep(0.5)  # Simulate processing time
        
        return {
            "type": "SkillResult",
            "req_id": req_id,
            "ok": True,
            "data": {
                "result": "success",
                "message": f"Executed {intent.get('name', 'unknown')} skill"
            },
            "status": "success"
        }
    
    def _handle_speak(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text-to-speech request"""
        req_id = message.get('req_id', 'unknown')
        text = message.get('text', '')
        
        print(f"🗣️ TTS request {req_id}: '{text[:50]}...'")
        
        # Simulate TTS processing
        time.sleep(1)  # Simulate processing time
        
        return {
            "type": "TTSResult",
            "req_id": req_id,
            "ok": True,
            "status": "success"
        }
    
    def _handle_transition(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state transition"""
        from_state = message.get('from', 'unknown')
        to_state = message.get('to', 'unknown')
        reason = message.get('reason', 'no reason')
        
        print(f"🔄 State transition: {from_state} → {to_state} ({reason})")
        
        self.state = to_state
        
        return {
            "type": "Transition",
            "status": "success",
            "from": from_state,
            "to": to_state,
            "reason": reason,
            "timestamp": time.time()
        }
    
    def _handle_health(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check request"""
        return {
            "type": "Health",
            "status": "healthy",
            "state": self.state,
            "clients": len(self.clients),
            "workers": len(self.workers),
            "uptime": time.time(),
            "timestamp": time.time()
        }
    
    def _handle_status(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request"""
        return {
            "type": "Status",
            "status": "running",
            "state": self.state,
            "clients": len(self.clients),
            "workers": len(self.workers),
            "socket_path": self.socket_path,
            "timestamp": time.time()
        }

def main():
    """Main function to run the IPC server"""
    print("🧪 Starting Nova IPC Server Test")
    print("=" * 60)
    
    # Create and start server
    server = NovaIPCServer()
    
    try:
        if server.start():
            print("✅ IPC Server started successfully")
            print("📡 Ready to accept worker connections")
            print("🔄 Server running... Press Ctrl+C to stop")
            
            # Keep server running
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    finally:
        server.stop()
        print("✅ Test completed")

if __name__ == "__main__":
    main()
