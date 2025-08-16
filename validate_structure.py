#!/usr/bin/env python3
"""
Validate Editorial Engine Platform Structure
"""

import os
from pathlib import Path

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (MISSING)")
        return False

def validate_structure():
    """Validate the complete platform structure."""
    print("🔍 Validating Editorial Engine Platform Structure...")
    print("=" * 60)
    
    checks = []
    
    # Core configuration files
    checks.append(check_file_exists(".env.example", "Environment template"))
    checks.append(check_file_exists("README.md", "Main documentation"))
    checks.append(check_file_exists("DEPLOYMENT.md", "Deployment guide"))
    checks.append(check_file_exists("start.sh", "Startup script"))
    checks.append(check_file_exists("test_platform.py", "Test script"))
    
    # Docker configuration
    checks.append(check_file_exists("deploy/docker-compose.yaml", "Docker Compose config"))
    checks.append(check_file_exists("deploy/prometheus/prometheus.yml", "Prometheus config"))
    checks.append(check_file_exists("deploy/grafana/datasources/prometheus.yml", "Grafana datasource"))
    
    # Vertical configurations
    checks.append(check_file_exists("configs/verticals/generic.yaml", "Generic vertical config"))
    checks.append(check_file_exists("configs/verticals/tax_de.yaml", "German tax vertical config"))
    checks.append(check_file_exists("configs/policies/sources-allowlist.txt", "Sources allowlist"))
    checks.append(check_file_exists("configs/policies/sources-denylist.txt", "Sources denylist"))
    
    # Shared libraries
    checks.append(check_file_exists("libs/common/__init__.py", "Common library"))
    checks.append(check_file_exists("libs/common/config.py", "Config loader"))
    checks.append(check_file_exists("libs/common/schemas.py", "Data schemas"))
    checks.append(check_file_exists("libs/common/fetch.py", "Content fetcher"))
    checks.append(check_file_exists("libs/common/extract.py", "Content extractor"))
    checks.append(check_file_exists("libs/common/dedupe.py", "Deduplication"))
    checks.append(check_file_exists("libs/common/chunking.py", "Text chunking"))
    checks.append(check_file_exists("libs/common/embed.py", "Embeddings"))
    
    checks.append(check_file_exists("libs/llm/__init__.py", "LLM library"))
    checks.append(check_file_exists("libs/llm/provider.py", "LLM provider interface"))
    
    checks.append(check_file_exists("libs/tavily_client/__init__.py", "Tavily client"))
    checks.append(check_file_exists("libs/tavily_client/client.py", "Tavily client implementation"))
    
    checks.append(check_file_exists("libs/seven011_client/__init__.py", "0711 client"))
    checks.append(check_file_exists("libs/seven011_client/client.py", "0711 client implementation"))
    
    # Applications
    apps = [
        "orchestrator",
        "worker-discovery", 
        "worker-intake",
        "worker-understanding",
        "worker-editorial",
        "worker-ingestion",
        "ui-search"
    ]
    
    for app in apps:
        checks.append(check_file_exists(f"apps/{app}/Dockerfile", f"{app} Dockerfile"))
        if app != "ui-search":
            checks.append(check_file_exists(f"apps/{app}/requirements.txt", f"{app} requirements"))
            if app == "orchestrator":
                checks.append(check_file_exists(f"apps/{app}/main.py", f"{app} main module"))
            else:
                checks.append(check_file_exists(f"apps/{app}/tasks.py", f"{app} tasks module"))
    
    # UI-specific files
    checks.append(check_file_exists("apps/ui-search/package.json", "UI package.json"))
    checks.append(check_file_exists("apps/ui-search/next.config.js", "Next.js config"))
    checks.append(check_file_exists("apps/ui-search/tailwind.config.js", "Tailwind config"))
    checks.append(check_file_exists("apps/ui-search/app/page.tsx", "UI main page"))
    checks.append(check_file_exists("apps/ui-search/app/api/search/route.ts", "Search API route"))
    checks.append(check_file_exists("apps/ui-search/app/components/SearchInterface.tsx", "Search component"))
    
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    print("=" * 60)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"✅ Files found: {passed}")
    print(f"❌ Files missing: {total - passed}")
    print(f"📈 Completion: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 Platform structure is complete!")
        print("🚀 Ready to deploy with: ./start.sh")
    else:
        print(f"\n⚠️  {total - passed} files are missing.")
        print("🔧 Please check the missing files above.")
    
    return passed == total

if __name__ == "__main__":
    validate_structure()