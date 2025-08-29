#!/usr/bin/env python3
"""
Test IPC Client for Nova Workers
Tests worker ↔ daemon communication
"""

import json
import socket
import time
import logging
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class NovaIPCClient:
    """Test IPC client for Nova workers"""
    
    def __init__(self, socket_path: str = "/tmp/nova.sock"):
        self.socket_path = socket_path
        self.socket = None
        self.connected = False
        self.request_id = 0
    
    def connect(self) -> bool:
        """Connect to the IPC server"""
        try:
            if not os.path.exists(self.socket_path):
                print(f"❌ Socket not found: {self.socket_path}")
                return False
            
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(self.socket_path)
            self.connected = True
            print(f"✅ Connected to IPC server at {self.socket_path}")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the IPC server"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        print("🔌 Disconnected from IPC server")
    
    def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a message and wait for response"""
        if not self.connected:
            print("❌ Not connected to server")
            return None
        
        try:
            # Send message
            message_json = json.dumps(message)
            self.socket.send(message_json.encode('utf-8'))
            print(f"📤 Sent: {message.get('type', 'Unknown')}")
            
            # Wait for response
            response_data = self.socket.recv(4096)
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                print(f"📥 Received: {response.get('type', 'Unknown')}")
                return response
            else:
                print("❌ No response received")
                return None
                
        except Exception as e:
            print(f"❌ Communication error: {e}")
            return None
    
    def test_wake_detected(self) -> bool:
        """Test wake word detection"""
        print("\n👂 Testing Wake Word Detection...")
        
        message = {
            "type": "WakeDetected",
            "ts": time.time()
        }
        
        response = self.send_message(message)
        if response and response.get('status') == 'success':
            print("   ✅ Wake word detection successful")
            return True
        else:
            print("   ❌ Wake word detection failed")
            return False
    
    def test_stt_request(self) -> bool:
        """Test speech-to-text request"""
        print("\n🎤 Testing Speech-to-Text Request...")
        
        self.request_id += 1
        message = {
            "type": "BeginSTT",
            "req_id": f"test_{self.request_id}",
            "max_seconds": 10
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'STTResult':
            print(f"   ✅ STT successful: '{response.get('text', '')}'")
            print(f"   📊 Confidence: {response.get('confidence', 0)}")
            return True
        else:
            print("   ❌ STT request failed")
            return False
    
    def test_nlp_routing(self, text: str) -> bool:
        """Test NLP routing"""
        print(f"\n🧠 Testing NLP Routing: '{text}'...")
        
        self.request_id += 1
        message = {
            "type": "NLPRoute",
            "req_id": f"test_{self.request_id}",
            "text": text
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'Intent':
            intent = response.get('intent', 'Unknown')
            slots = response.get('slots', {})
            print(f"   ✅ NLP successful: Intent={intent}, Slots={slots}")
            return True
        else:
            print("   ❌ NLP routing failed")
            return False
    
    def test_skill_execution(self, skill_name: str) -> bool:
        """Test skill execution"""
        print(f"\n⚡ Testing Skill Execution: {skill_name}...")
        
        self.request_id += 1
        message = {
            "type": "ExecuteSkill",
            "req_id": f"test_{self.request_id}",
            "intent": {
                "name": skill_name,
                "slots": {}
            }
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'SkillResult':
            success = response.get('ok', False)
            if success:
                print("   ✅ Skill execution successful")
                return True
            else:
                print("   ❌ Skill execution failed")
                return False
        else:
            print("   ❌ Skill execution request failed")
            return False
    
    def test_tts_request(self, text: str) -> bool:
        """Test text-to-speech request"""
        print(f"\n🗣️ Testing Text-to-Speech: '{text[:30]}...'...")
        
        self.request_id += 1
        message = {
            "type": "Speak",
            "req_id": f"test_{self.request_id}",
            "text": text
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'TTSResult':
            success = response.get('ok', False)
            if success:
                print("   ✅ TTS request successful")
                return True
            else:
                print("   ❌ TTS request failed")
                return False
        else:
            print("   ❌ TTS request failed")
            return False
    
    def test_state_transition(self, from_state: str, to_state: str, reason: str) -> bool:
        """Test state transition"""
        print(f"\n🔄 Testing State Transition: {from_state} → {to_state}...")
        
        message = {
            "type": "Transition",
            "from": from_state,
            "to": to_state,
            "reason": reason
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'Transition':
            print("   ✅ State transition successful")
            return True
        else:
            print("   ❌ State transition failed")
            return False
    
    def test_health_check(self) -> bool:
        """Test health check"""
        print("\n🏥 Testing Health Check...")
        
        message = {
            "type": "Health"
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'Health':
            status = response.get('status', 'unknown')
            state = response.get('state', 'unknown')
            clients = response.get('clients', 0)
            print(f"   ✅ Health check successful: {status}, State: {state}, Clients: {clients}")
            return True
        else:
            print("   ❌ Health check failed")
            return False
    
    def test_status_request(self) -> bool:
        """Test status request"""
        print("\n📊 Testing Status Request...")
        
        message = {
            "type": "Status"
        }
        
        response = self.send_message(message)
        if response and response.get('type') == 'Status':
            status = response.get('status', 'unknown')
            state = response.get('state', 'unknown')
            socket_path = response.get('socket_path', 'unknown')
            print(f"   ✅ Status request successful: {status}, State: {state}, Socket: {socket_path}")
            return True
        else:
            print("   ❌ Status request failed")
            return False

def run_comprehensive_test():
    """Run comprehensive IPC communication test"""
    print("🧪 Starting Nova IPC Client Comprehensive Test")
    print("=" * 60)
    
    # Create client
    client = NovaIPCClient()
    
    try:
        # Connect to server
        if not client.connect():
            print("❌ Cannot proceed without connection")
            return False
        
        # Test 1: Basic Communication
        print("\n1️⃣ Testing Basic Communication...")
        
        health_success = client.test_health_check()
        status_success = client.test_status_request()
        
        if not (health_success and status_success):
            print("   ❌ Basic communication failed")
            return False
        
        # Test 2: Wake Word Flow
        print("\n2️⃣ Testing Wake Word Flow...")
        
        wake_success = client.test_wake_detected()
        if not wake_success:
            print("   ❌ Wake word detection failed")
            return False
        
        # Test 3: STT Request
        print("\n3️⃣ Testing Speech-to-Text...")
        
        stt_success = client.test_stt_request()
        if not stt_success:
            print("   ❌ STT request failed")
            return False
        
        # Test 4: NLP Routing
        print("\n4️⃣ Testing NLP Routing...")
        
        nlp_tests = [
            "What's my schedule for today?",
            "Play some music on Spotify",
            "Turn on Do Not Disturb mode"
        ]
        
        nlp_success = True
        for text in nlp_tests:
            if not client.test_nlp_routing(text):
                nlp_success = False
                break
        
        if not nlp_success:
            print("   ❌ NLP routing failed")
            return False
        
        # Test 5: Skill Execution
        print("\n5️⃣ Testing Skill Execution...")
        
        skill_tests = ["GetSchedule", "ControlMusic", "ControlFocus"]
        
        skill_success = True
        for skill in skill_tests:
            if not client.test_skill_execution(skill):
                skill_success = False
                break
        
        if not skill_success:
            print("   ❌ Skill execution failed")
            return False
        
        # Test 6: TTS Request
        print("\n6️⃣ Testing Text-to-Speech...")
        
        tts_text = "Hello Sir, I've retrieved your schedule for today. You have 4 events remaining."
        tts_success = client.test_tts_request(tts_text)
        
        if not tts_success:
            print("   ❌ TTS request failed")
            return False
        
        # Test 7: State Transitions
        print("\n7️⃣ Testing State Transitions...")
        
        transition_tests = [
            ("IDLE", "LISTENING", "Wake word detected"),
            ("LISTENING", "PROCESSING", "User input received"),
            ("PROCESSING", "SPEAKING", "Response ready"),
            ("SPEAKING", "IDLE", "Response complete")
        ]
        
        transition_success = True
        for from_state, to_state, reason in transition_tests:
            if not client.test_state_transition(from_state, to_state, reason):
                transition_success = False
                break
        
        if not transition_success:
            print("   ❌ State transitions failed")
            return False
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE IPC TEST RESULTS")
        print("=" * 60)
        print("   ✅ All communication tests PASSED!")
        print("   🎉 IPC system is ready for integration!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        client.disconnect()

if __name__ == "__main__":
    run_comprehensive_test()
