#!/usr/bin/env python3
"""
Fitness Functions Testing Strategy Script

This script provides an automated testing strategy for the fitness functions application.
It handles:
- Setting up Python virtual environment
- Starting backend and frontend servers
- Opening browser (with WSL workaround)
- Running tests
"""

import os
import sys
import subprocess
import time
import platform
import webbrowser
import signal
import threading
from pathlib import Path

class FitnessFunctionsTestRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.api_dir = self.base_dir / "api"
        self.ui_dir = self.base_dir / "ui"
        self.venv_dir = self.api_dir / "venv"
        self.backend_process = None
        self.frontend_process = None
        self.frontend_url = "http://localhost:3003"
        self.backend_url = "http://localhost:8000"
        
    def is_wsl(self):
        """Check if running in WSL environment."""
        return "microsoft" in platform.uname().release.lower()
    
    def open_browser(self, url):
        """Open browser with WSL workaround if needed."""
        print(f"Opening browser to: {url}")
        
        if self.is_wsl():
            # WSL workaround - use Windows explorer to open the URL
            try:
                subprocess.run(["/mnt/c/Windows/explorer.exe", url], 
                             check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Browser opened via WSL workaround")
            except subprocess.CalledProcessError:
                print("WSL browser opening failed, trying fallback method")
                # Fallback to cmd.exe
                try:
                    subprocess.run(["/mnt/c/Windows/System32/cmd.exe", "/c", "start", url], 
                                 check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    print("All WSL browser methods failed")
        else:
            # Standard browser opening
            webbrowser.open_new_tab(url)
    
    def setup_venv(self):
        """Set up Python virtual environment for API."""
        print("Setting up Python virtual environment...")
        
        if not self.venv_dir.exists():
            print("Creating new virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], 
                         cwd=self.api_dir, check=True)
        else:
            print("Virtual environment already exists")
            
        # Get the correct python executable path
        if os.name == 'nt':
            python_exe = self.venv_dir / "Scripts" / "python.exe"
            pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = self.venv_dir / "bin" / "python"
            pip_exe = self.venv_dir / "bin" / "pip"
            
        # Install requirements
        print("Installing Python dependencies...")
        subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], 
                      cwd=self.api_dir, check=True)
        
        # Ensure settings.ini exists
        settings_file = self.api_dir / "settings.ini"
        if not settings_file.exists():
            print("Creating settings.ini from example...")
            subprocess.run(["cp", "settings.example.ini", "settings.ini"], 
                          cwd=self.api_dir, check=True)
        
        return python_exe
    
    def start_backend(self, python_exe):
        """Start the FastAPI backend server."""
        print("Starting backend server...")
        
        # Start uvicorn server
        cmd = [str(python_exe), "-m", "uvicorn", "app:app", "--reload", "--port", "8000"]
        self.backend_process = subprocess.Popen(
            cmd, 
            cwd=self.api_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("Waiting for backend server to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                import requests
                response = requests.get(f"{self.backend_url}/", timeout=1)
                if response.status_code == 200:
                    print("Backend server is ready!")
                    return True
            except:
                pass
            time.sleep(1)
            
        print("Backend server failed to start in time")
        return False
    
    def start_frontend(self):
        """Start the React frontend server."""
        print("Starting frontend server...")
        
        # Install npm packages if needed
        if not (self.ui_dir / "node_modules").exists():
            print("Installing npm packages...")
            subprocess.run(["npm", "install"], cwd=self.ui_dir, check=True)
        
        # Start npm server
        env = os.environ.copy()
        env["PORT"] = "3003"
        
        self.frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=self.ui_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # Wait for server to start
        print("Waiting for frontend server to start...")
        for i in range(60):  # Wait up to 60 seconds for React to compile
            try:
                import requests
                response = requests.get(self.frontend_url, timeout=1)
                if response.status_code == 200:
                    print("Frontend server is ready!")
                    return True
            except:
                pass
            time.sleep(1)
            
        print("Frontend server failed to start in time")
        return False
    
    def run_tests(self):
        """Run the test suite."""
        print("Running React tests...")
        
        # Run npm test
        test_process = subprocess.run(
            ["npm", "test", "--", "--watchAll=false", "--coverage"],
            cwd=self.ui_dir,
            capture_output=True,
            text=True
        )
        
        print("Test Results:")
        print(test_process.stdout)
        if test_process.stderr:
            print("Test Errors:")
            print(test_process.stderr)
            
        return test_process.returncode == 0
    
    def run_smoke_test(self):
        """Run basic smoke tests to verify the application is working."""
        print("Running smoke tests...")
        
        try:
            import requests
            
            # Test backend health
            print("Testing backend health...")
            backend_response = requests.get(f"{self.backend_url}/", timeout=5)
            print(f"Backend status: {backend_response.status_code}")
            
            # Test GraphQL endpoint
            print("Testing GraphQL endpoint...")
            graphql_response = requests.get(f"{self.backend_url}/graphql", timeout=5)
            print(f"GraphQL status: {graphql_response.status_code}")
            
            # Test frontend
            print("Testing frontend...")
            frontend_response = requests.get(self.frontend_url, timeout=5)
            print(f"Frontend status: {frontend_response.status_code}")
            
            print("✅ All smoke tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Smoke tests failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up running processes."""
        print("Cleaning up...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_process.wait()
            
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                self.frontend_process.wait()
    
    def run_full_test(self):
        """Run the complete testing workflow."""
        print("🚀 Starting Fitness Functions Testing Strategy")
        print("=" * 50)
        
        try:
            # Setup
            python_exe = self.setup_venv()
            
            # Start servers
            if not self.start_backend(python_exe):
                return False
                
            if not self.start_frontend():
                return False
            
            # Open browser
            self.open_browser(self.frontend_url)
            
            # Run tests
            smoke_passed = self.run_smoke_test()
            unit_tests_passed = self.run_tests()
            
            # Wait for user interaction
            print("\n" + "=" * 50)
            print("🎯 Testing Environment Ready!")
            print(f"Frontend: {self.frontend_url}")
            print(f"Backend: {self.backend_url}")
            print(f"GraphQL: {self.backend_url}/graphql")
            print("=" * 50)
            
            if smoke_passed and unit_tests_passed:
                print("✅ All tests passed! Press Enter to continue or Ctrl+C to exit...")
            else:
                print("⚠️  Some tests failed. Check the output above.")
                print("Press Enter to continue or Ctrl+C to exit...")
                
            input()
            
            return smoke_passed and unit_tests_passed
            
        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-only":
        # Quick smoke test mode
        runner = FitnessFunctionsTestRunner()
        try:
            python_exe = runner.setup_venv()
            if runner.start_backend(python_exe) and runner.start_frontend():
                success = runner.run_smoke_test()
                sys.exit(0 if success else 1)
        finally:
            runner.cleanup()
    else:
        # Full test mode
        runner = FitnessFunctionsTestRunner()
        success = runner.run_full_test()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()