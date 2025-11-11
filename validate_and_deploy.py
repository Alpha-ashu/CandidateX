#!/usr/bin/env python3
"""
CandidateX - Complete Validation and Deployment Script
This script validates the entire application stack and prepares it for deployment.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ValidationReport:
    """Tracks validation results."""
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
        self.skipped: List[str] = []
    
    def add_pass(self, test: str):
        self.passed.append(test)
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {test}")
    
    def add_fail(self, test: str, reason: str = ""):
        self.failed.append(f"{test}: {reason}" if reason else test)
        print(f"{Colors.FAIL}✗{Colors.ENDC} {test}")
        if reason:
            print(f"  {Colors.FAIL}Reason: {reason}{Colors.ENDC}")
    
    def add_warning(self, test: str, reason: str = ""):
        self.warnings.append(f"{test}: {reason}" if reason else test)
        print(f"{Colors.WARNING}⚠{Colors.ENDC} {test}")
        if reason:
            print(f"  {Colors.WARNING}Warning: {reason}{Colors.ENDC}")
    
    def add_skip(self, test: str, reason: str = ""):
        self.skipped.append(f"{test}: {reason}" if reason else test)
        print(f"{Colors.OKCYAN}○{Colors.ENDC} {test} (skipped)")
        if reason:
            print(f"  {Colors.OKCYAN}Reason: {reason}{Colors.ENDC}")
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        print(f"{Colors.OKGREEN}Passed:{Colors.ENDC} {len(self.passed)}")
        print(f"{Colors.FAIL}Failed:{Colors.ENDC} {len(self.failed)}")
        print(f"{Colors.WARNING}Warnings:{Colors.ENDC} {len(self.warnings)}")
        print(f"{Colors.OKCYAN}Skipped:{Colors.ENDC} {len(self.skipped)}")
        
        if self.failed:
            print(f"\n{Colors.FAIL}Failed Tests:{Colors.ENDC}")
            for fail in self.failed:
                print(f"  - {fail}")
        
        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        total_tests = len(self.passed) + len(self.failed) + len(self.warnings)
        if total_tests > 0:
            success_rate = (len(self.passed) / total_tests) * 100
            print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        return len(self.failed) == 0

class CandidateXValidator:
    """Main validator class for CandidateX application."""
    
    def __init__(self):
        self.report = ValidationReport()
        self.project_root = Path.cwd()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root
        
    def print_header(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None, 
                   timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a shell command and return success status and output."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_file_exists(self, filepath: Path, description: str) -> bool:
        """Check if a file exists."""
        if filepath.exists():
            self.report.add_pass(f"{description} exists")
            return True
        else:
            self.report.add_fail(f"{description} not found", str(filepath))
            return False
    
    def validate_project_structure(self):
        """Validate project directory structure."""
        self.print_header("Phase 1: Project Structure Validation")
        
        # Check critical files
        critical_files = [
            (self.project_root / "package.json", "Frontend package.json"),
            (self.project_root / "tsconfig.json", "TypeScript config"),
            (self.project_root / "vite.config.ts", "Vite config"),
            (self.project_root / "index.html", "Frontend entry HTML"),
            (self.backend_dir / "requirements.txt", "Backend requirements"),
            (self.backend_dir / "app" / "main.py", "Backend main application"),
            (self.backend_dir / "app" / "config.py", "Backend configuration"),
            (self.backend_dir / "Dockerfile", "Backend Dockerfile"),
            (self.backend_dir / "docker-compose.yml", "Docker Compose config"),
            (self.backend_dir / "pytest.ini", "Pytest configuration"),
        ]
        
        for filepath, description in critical_files:
            self.check_file_exists(filepath, description)
        
        # Check critical directories
        critical_dirs = [
            (self.project_root / "src", "Frontend source directory"),
            (self.backend_dir / "app", "Backend app directory"),
            (self.backend_dir / "tests", "Backend tests directory"),
            (self.project_root / "src" / "pages", "Frontend pages directory"),
            (self.project_root / "src" / "components", "Frontend components directory"),
        ]
        
        for dirpath, description in critical_dirs:
            if dirpath.exists() and dirpath.is_dir():
                self.report.add_pass(f"{description} exists")
            else:
                self.report.add_fail(f"{description} not found", str(dirpath))
    
    def validate_backend_dependencies(self):
        """Validate backend Python dependencies."""
        self.print_header("Phase 2: Backend Dependencies Validation")
        
        # Check Python version
        success, stdout, stderr = self.run_command(["python", "--version"])
        if success:
            version = stdout.strip()
            self.report.add_pass(f"Python installed: {version}")
            if "3.9" in version or "3.10" in version or "3.11" in version or "3.12" in version:
                self.report.add_pass("Python version compatible (3.9+)")
            else:
                self.report.add_warning("Python version", "Recommended Python 3.9+")
        else:
            self.report.add_fail("Python not found or not in PATH")
            return
        
        # Check pip
        success, stdout, stderr = self.run_command(["pip", "--version"])
        if success:
            self.report.add_pass(f"pip installed: {stdout.strip()}")
        else:
            self.report.add_fail("pip not found")
            return
        
        # Check if virtual environment exists
        venv_paths = [
            self.backend_dir / "venv",
            self.backend_dir / ".venv",
            self.project_root / "venv",
            self.project_root / ".venv"
        ]
        
        venv_exists = any(p.exists() for p in venv_paths)
        if venv_exists:
            self.report.add_pass("Virtual environment found")
        else:
            self.report.add_warning("Virtual environment not found", 
                                   "Consider creating one with: python -m venv venv")
        
        # Try to import critical packages
        critical_packages = [
            "fastapi",
            "uvicorn",
            "motor",
            "redis",
            "pydantic",
            "pytest"
        ]
        
        for package in critical_packages:
            success, stdout, stderr = self.run_command(
                ["python", "-c", f"import {package}; print({package}.__version__)"]
            )
            if success:
                version = stdout.strip()
                self.report.add_pass(f"{package} installed: {version}")
            else:
                self.report.add_fail(f"{package} not installed", 
                                    "Run: pip install -r backend/requirements.txt")
    
    def validate_frontend_dependencies(self):
        """Validate frontend Node.js dependencies."""
        self.print_header("Phase 3: Frontend Dependencies Validation")
        
        # Check Node.js
        success, stdout, stderr = self.run_command(["node", "--version"])
        if success:
            version = stdout.strip()
            self.report.add_pass(f"Node.js installed: {version}")
        else:
            self.report.add_fail("Node.js not found or not in PATH")
            return
        
        # Check npm
        success, stdout, stderr = self.run_command(["npm", "--version"])
        if success:
            version = stdout.strip()
            self.report.add_pass(f"npm installed: {version}")
        else:
            self.report.add_fail("npm not found")
            return
        
        # Check if node_modules exists
        node_modules = self.project_root / "node_modules"
        if node_modules.exists():
            self.report.add_pass("node_modules directory exists")
        else:
            self.report.add_warning("node_modules not found", 
                                   "Run: npm install")
        
        # Check package-lock.json
        if (self.project_root / "package-lock.json").exists():
            self.report.add_pass("package-lock.json exists")
        else:
            self.report.add_warning("package-lock.json not found")
    
    def validate_database_services(self):
        """Validate database services (MongoDB and Redis)."""
        self.print_header("Phase 4: Database Services Validation")
        
        # Check MongoDB
        print("Checking MongoDB connection...")
        try:
            import pymongo
            from pymongo import MongoClient
            
            # Try to connect to MongoDB
            client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            client.server_info()
            self.report.add_pass("MongoDB is running and accessible")
            client.close()
        except ImportError:
            self.report.add_warning("pymongo not installed", 
                                   "Cannot verify MongoDB connection")
        except Exception as e:
            self.report.add_fail("MongoDB connection failed", 
                                f"Ensure MongoDB is running on localhost:27017")
        
        # Check Redis
        print("Checking Redis connection...")
        try:
            import redis
            
            # Try to connect to Redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            r.ping()
            self.report.add_pass("Redis is running and accessible")
            r.close()
        except ImportError:
            self.report.add_warning("redis package not installed", 
                                   "Cannot verify Redis connection")
        except Exception as e:
            self.report.add_fail("Redis connection failed", 
                                f"Ensure Redis is running on localhost:6379")
    
    def validate_backend_tests(self):
        """Run backend tests."""
        self.print_header("Phase 5: Backend Tests Validation")
        
        print("Running backend tests (this may take a few minutes)...\n")
        
        # Run pytest
        success, stdout, stderr = self.run_command(
            ["pytest", "-v", "--tb=short", "-x"],
            cwd=self.backend_dir,
            timeout=600
        )
        
        if success:
            self.report.add_pass("All backend tests passed")
            
            # Try to extract test count
            if "passed" in stdout:
                self.report.add_pass(f"Test results: {stdout.split('passed')[0].split()[-1]} tests passed")
        else:
            self.report.add_fail("Backend tests failed", 
                                "Check test output above for details")
            if stderr:
                print(f"\n{Colors.FAIL}Error output:{Colors.ENDC}")
                print(stderr[:1000])  # Print first 1000 chars
    
    def validate_backend_server(self):
        """Validate backend server can start."""
        self.print_header("Phase 6: Backend Server Validation")
        
        print("Testing backend server startup (will timeout after 30 seconds)...\n")
        
        # Try to start the server briefly
        try:
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for server to start
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                self.report.add_pass("Backend server started successfully")
                
                # Try to hit health endpoint
                try:
                    import requests
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        self.report.add_pass("Health endpoint responding")
                        data = response.json()
                        print(f"  Server status: {data.get('status', 'unknown')}")
                    else:
                        self.report.add_warning("Health endpoint returned non-200 status")
                except ImportError:
                    self.report.add_skip("Health endpoint check", "requests package not installed")
                except Exception as e:
                    self.report.add_warning("Health endpoint check failed", str(e))
                
                # Terminate the server
                process.terminate()
                process.wait(timeout=5)
            else:
                self.report.add_fail("Backend server failed to start")
                stdout, stderr = process.communicate()
                if stderr:
                    print(f"\n{Colors.FAIL}Error output:{Colors.ENDC}")
                    print(stderr[:1000])
        
        except Exception as e:
            self.report.add_fail("Backend server validation failed", str(e))
    
    def validate_frontend_build(self):
        """Validate frontend can build."""
        self.print_header("Phase 7: Frontend Build Validation")
        
        print("Building frontend (this may take a few minutes)...\n")
        
        # Run npm build
        success, stdout, stderr = self.run_command(
            ["npm", "run", "build"],
            cwd=self.frontend_dir,
            timeout=300
        )
        
        if success:
            self.report.add_pass("Frontend build successful")
            
            # Check if build directory exists
            build_dir = self.project_root / "build"
            dist_dir = self.project_root / "dist"
            
            if build_dir.exists():
                self.report.add_pass("Build output directory created (build/)")
                
                # Check for index.html
                if (build_dir / "index.html").exists():
                    self.report.add_pass("index.html generated in build output")
                else:
                    self.report.add_warning("index.html not found in build output")
            elif dist_dir.exists():
                self.report.add_pass("Build output directory created (dist/)")
                
                if (dist_dir / "index.html").exists():
                    self.report.add_pass("index.html generated in build output")
                else:
                    self.report.add_warning("index.html not found in build output")
            else:
                self.report.add_warning("Build output directory not found")
        else:
            self.report.add_fail("Frontend build failed", 
                                "Check build output above for details")
            if stderr:
                print(f"\n{Colors.FAIL}Error output:{Colors.ENDC}")
                print(stderr[:1000])
    
    def validate_docker_setup(self):
        """Validate Docker configuration."""
        self.print_header("Phase 8: Docker Configuration Validation")
        
        # Check if Docker is installed
        success, stdout, stderr = self.run_command(["docker", "--version"])
        if success:
            version = stdout.strip()
            self.report.add_pass(f"Docker installed: {version}")
        else:
            self.report.add_skip("Docker validation", "Docker not installed")
            return
        
        # Check docker-compose
        success, stdout, stderr = self.run_command(["docker-compose", "--version"])
        if not success:
            success, stdout, stderr = self.run_command(["docker", "compose", "version"])
        
        if success:
            version = stdout.strip()
            self.report.add_pass(f"Docker Compose available: {version}")
        else:
            self.report.add_warning("Docker Compose not found")
        
        # Validate Dockerfile
        dockerfile = self.backend_dir / "Dockerfile"
        if dockerfile.exists():
            self.report.add_pass("Dockerfile exists")
            
            # Check Dockerfile content
            content = dockerfile.read_text()
            if "FROM python:" in content:
                self.report.add_pass("Dockerfile has valid base image")
            if "COPY requirements.txt" in content:
                self.report.add_pass("Dockerfile copies requirements")
            if "CMD" in content or "ENTRYPOINT" in content:
                self.report.add_pass("Dockerfile has startup command")
        else:
            self.report.add_fail("Dockerfile not found")
        
        # Validate docker-compose.yml
        compose_file = self.backend_dir / "docker-compose.yml"
        if compose_file.exists():
            self.report.add_pass("docker-compose.yml exists")
            
            # Check compose file content
            content = compose_file.read_text()
            if "mongodb:" in content:
                self.report.add_pass("docker-compose includes MongoDB service")
            if "redis:" in content:
                self.report.add_pass("docker-compose includes Redis service")
            if "app:" in content:
                self.report.add_pass("docker-compose includes app service")
        else:
            self.report.add_fail("docker-compose.yml not found")
    
    def validate_security_configuration(self):
        """Validate security configuration."""
        self.print_header("Phase 9: Security Configuration Validation")
        
        # Check for .env file (should not be in git)
        env_file = self.backend_dir / ".env"
        if env_file.exists():
            self.report.add_pass(".env file exists for configuration")
            
            # Check if .env is in .gitignore
            gitignore = self.project_root / ".gitignore"
            if gitignore.exists():
                content = gitignore.read_text()
                if ".env" in content:
                    self.report.add_pass(".env is in .gitignore")
                else:
                    self.report.add_warning(".env should be in .gitignore")
        else:
            self.report.add_warning(".env file not found", 
                                   "Create from .env.example for local development")
        
        # Check config.py for security settings
        config_file = self.backend_dir / "app" / "config.py"
        if config_file.exists():
            content = config_file.read_text()
            
            if "SECRET_KEY" in content:
                self.report.add_pass("SECRET_KEY configuration present")
            if "JWT_SECRET_KEY" in content:
                self.report.add_pass("JWT_SECRET_KEY configuration present")
            if "BCRYPT_ROUNDS" in content:
                self.report.add_pass("Password hashing configuration present")
            if "CORS_ORIGINS" in content:
                self.report.add_pass("CORS configuration present")
    
    def generate_deployment_checklist(self):
        """Generate deployment checklist."""
        self.print_header("Phase 10: Deployment Checklist")
        
        checklist = [
            "✓ Set production SECRET_KEY (not default)",
            "✓ Set production JWT_SECRET_KEY (not default)",
            "✓ Configure production MongoDB URL",
            "✓ Configure production Redis URL",
            "✓ Set up AI API keys (Google Gemini/OpenAI)",
            "✓ Configure email service (SMTP)",
            "✓ Set up cloud storage (AWS S3/Firebase) - optional",
            "✓ Configure domain and SSL certificates",
            "✓ Set up monitoring (Sentry) - optional",
            "✓ Configure firewall rules",
            "✓ Set up database backups",
            "✓ Configure log rotation",
            "✓ Set up uptime monitoring",
            "✓ Test all endpoints in production",
            "✓ Verify SSL/HTTPS working",
            "✓ Test from different devices/browsers",
        ]
        
        print(f"{Colors.BOLD}Pre-Deployment Checklist:{Colors.ENDC}\n")
        for item in checklist:
            print(f"  {item}")
        
        print(f"\n{Colors.BOLD}Deployment Commands:{Colors.ENDC}\n")
        print("  # Backend (with Docker):")
        print("  cd backend")
        print("  docker-compose up -d")
        print()
        print("  # Backend (without Docker):")
        print("  cd backend")
        print("  gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000")
        print()
        print("  # Frontend:")
        print("  npm run build")
        print("  # Serve the build/ or dist/ directory with a web server")
        print()
    
    def run_all_validations(self):
        """Run all validation phases."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                            ║")
        print("║                   CandidateX Validation & Deployment Tool                  ║")
        print("║                                                                            ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        # Run all validation phases
        self.validate_project_structure()
        self.validate_backend_dependencies()
        self.validate_frontend_dependencies()
        self.validate_database_services()
        
        # Ask user if they want to run tests (can be slow)
        print(f"\n{Colors.BOLD}Run backend tests? This may take several minutes. (y/n): {Colors.ENDC}", end="")
        response = input().strip().lower()
        if response == 'y':
            self.validate_backend_tests()
        else:
            self.report.add_skip("Backend tests", "Skipped by user")
        
        # Ask user if they want to test server startup
        print(f"\n{Colors.BOLD}Test backend server startup? (y/n): {Colors.ENDC}", end="")
        response = input().strip().lower()
        if response == 'y':
            self.validate_backend_server()
        else:
            self.report.add_skip("Backend server test", "Skipped by user")
        
        # Ask user if they want to build frontend
        print(f"\n{Colors.BOLD}Build frontend? This may take several minutes. (y/n): {Colors.ENDC}", end="")
        response = input().strip().lower()
        if response == 'y':
            self.validate_frontend_build()
        else:
            self.report.add_skip("Frontend build", "Skipped by user")
        
        self.validate_docker_setup()
        self.validate_security_configuration()
        self.generate_deployment_checklist()
        
        # Print final summary
        success = self.report.print_summary()
        
        if success:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ All critical validations passed!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}The application is ready for deployment.{Colors.ENDC}\n")
            return 0
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}✗ Some validations failed.{Colors.ENDC}")
            print(f"{Colors.FAIL}Please fix the issues before deploying.{Colors.ENDC}\n")
            return 1

def main():
    """Main entry point."""
    validator = CandidateXValidator()
    exit_code = validator.run_all_validations()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
