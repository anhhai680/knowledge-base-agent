#!/usr/bin/env python3
"""
Utility script to clean up Chroma database issues
"""

import os
import shutil
import time
import subprocess
from pathlib import Path

def cleanup_chroma_directories():
    """Clean up all Chroma database directories that might be causing issues"""
    
    print("🧹 Chroma Database Cleanup Utility")
    print("=" * 50)
    
    # List of potential Chroma database directories
    chroma_dirs = [
        "./chroma_db",
        "./chroma_db_new_*",
        "./chroma_db_reset_*",
        "./chroma_db_fresh_*",
        "./test_chroma_db*"
    ]
    
    # Find all matching directories
    found_dirs = []
    for pattern in chroma_dirs:
        if "*" in pattern:
            # Handle wildcard patterns
            base_pattern = pattern.replace("*", "")
            if os.path.exists(base_pattern):
                found_dirs.append(base_pattern)
            
            # Look for timestamped directories
            parent_dir = Path(".")
            for item in parent_dir.iterdir():
                if item.is_dir() and item.name.startswith(base_pattern.replace("./", "")):
                    found_dirs.append(str(item))
        else:
            if os.path.exists(pattern):
                found_dirs.append(pattern)
    
    if not found_dirs:
        print("✅ No Chroma database directories found to clean up.")
        return
    
    print(f"Found {len(found_dirs)} Chroma database directories:")
    for dir_path in found_dirs:
        print(f"  - {dir_path}")
    
    # Check for processes using these directories
    print("\n🔍 Checking for processes using Chroma directories...")
    try:
        import psutil
        
        for dir_path in found_dirs:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any(dir_path in ' '.join(cmdline) for dir_path in found_dirs):
                        print(f"  ⚠️  Process {proc.info['pid']} ({proc.info['name']}) might be using Chroma")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except ImportError:
        print("  ℹ️  psutil not available, skipping process check")
    
    # Ask for confirmation
    print(f"\n⚠️  This will permanently delete {len(found_dirs)} Chroma database directories.")
    response = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled.")
        return
    
    # Perform cleanup
    print("\n🗑️  Starting cleanup...")
    successful_removals = 0
    failed_removals = 0
    
    for dir_path in found_dirs:
        try:
            print(f"  Removing {dir_path}...")
            
            # Try graceful removal first
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    print(f"    ✅ Successfully removed {dir_path}")
                    successful_removals += 1
                except PermissionError:
                    print(f"    ⚠️  Permission denied, trying force removal...")
                    # Try force removal with system commands
                    try:
                        if os.name == 'nt':  # Windows
                            subprocess.run(['rmdir', '/s', '/q', dir_path], shell=True, check=True)
                        else:  # Unix-like
                            subprocess.run(['rm', '-rf', dir_path], check=True)
                        print(f"    ✅ Force removed {dir_path}")
                        successful_removals += 1
                    except subprocess.CalledProcessError as e:
                        print(f"    ❌ Force removal failed: {e}")
                        failed_removals += 1
                except OSError as e:
                    if "Device or resource busy" in str(e):
                        print(f"    ⚠️  Resource busy, waiting and retrying...")
                        time.sleep(2)
                        try:
                            shutil.rmtree(dir_path)
                            print(f"    ✅ Successfully removed {dir_path} after retry")
                            successful_removals += 1
                        except Exception as retry_e:
                            print(f"    ❌ Retry failed: {retry_e}")
                            failed_removals += 1
                    else:
                        print(f"    ❌ Failed to remove {dir_path}: {e}")
                        failed_removals += 1
            else:
                print(f"    ℹ️  Directory {dir_path} no longer exists")
                successful_removals += 1
                
        except Exception as e:
            print(f"    ❌ Error processing {dir_path}: {e}")
            failed_removals += 1
    
    # Summary
    print(f"\n📊 Cleanup Summary:")
    print(f"  ✅ Successfully removed: {successful_removals}")
    print(f"  ❌ Failed to remove: {failed_removals}")
    
    if failed_removals == 0:
        print("🎉 All Chroma database directories cleaned up successfully!")
    else:
        print("⚠️  Some directories could not be removed. You may need to:")
        print("   - Restart your application")
        print("   - Check for running processes using these directories")
        print("   - Manually remove the remaining directories")

def check_system_resources():
    """Check system resources that might affect Chroma database operations"""
    
    print("\n🔍 System Resource Check")
    print("=" * 30)
    
    try:
        import psutil
        
        # Check disk space
        disk_usage = psutil.disk_usage('.')
        print(f"💾 Disk space:")
        print(f"  Total: {disk_usage.total / (1024**3):.2f} GB")
        print(f"  Used: {disk_usage.used / (1024**3):.2f} GB")
        print(f"  Free: {disk_usage.free / (1024**3):.2f} GB")
        print(f"  Usage: {disk_usage.percent:.1f}%")
        
        # Check memory
        memory = psutil.virtual_memory()
        print(f"🧠 Memory:")
        print(f"  Total: {memory.total / (1024**3):.2f} GB")
        print(f"  Available: {memory.available / (1024**3):.2f} GB")
        print(f"  Usage: {memory.percent:.1f}%")
        
        # Check file descriptors (Unix-like systems)
        if hasattr(psutil, 'num_fds'):
            try:
                num_fds = psutil.Process().num_fds()
                print(f"📁 Open file descriptors: {num_fds}")
            except (psutil.AccessDenied, AttributeError):
                pass
                
    except ImportError:
        print("ℹ️  psutil not available, skipping system resource check")

if __name__ == "__main__":
    try:
        cleanup_chroma_directories()
        check_system_resources()
        
        print("\n✨ Cleanup utility completed!")
        print("\n💡 Next steps:")
        print("   1. Restart your application")
        print("   2. The Chroma store will create a fresh database")
        print("   3. Your documents will be re-indexed with the correct dimensions")
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user.")
    except Exception as e:
        print(f"\n💥 Cleanup utility failed: {e}")
        import traceback
        traceback.print_exc()
