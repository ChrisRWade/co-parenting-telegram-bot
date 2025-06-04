#!/usr/bin/env python3
"""Test script to verify bot setup and configuration."""

from __future__ import annotations

import sys
from pathlib import Path

def test_imports() -> bool:
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import telegram
        print(f"✅ python-telegram-bot: {telegram.__version__}")
    except ImportError as e:
        print(f"❌ python-telegram-bot import failed: {e}")
        return False
    
    try:
        import openai
        print(f"✅ openai: {openai.__version__}")
    except ImportError as e:
        print(f"❌ openai import failed: {e}")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    try:
        import requests
        print(f"✅ requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    return True


def test_project_structure() -> bool:
    """Test that all required files exist."""
    print("\nTesting project structure...")
    
    required_files = [
        "README.md",
        "requirements.txt",
        "env.example",
        ".gitignore",
        "config.py",
        "bot/__init__.py",
        "bot/main.py",
        "bot/filters.py",
        "bot/handlers.py",
        "bot/logging.cfg",
        "deployment/coparentbot.service",
    ]
    
    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def test_configuration() -> bool:
    """Test configuration loading and moderation profiles."""
    print("\nTesting configuration...")
    
    try:
        from config import config, MODERATION_PROFILES
        print("✅ Config module imported successfully")
        
        # Test moderation profiles
        print(f"✅ Available moderation profiles: {list(MODERATION_PROFILES.keys())}")
        
        # Test that config validation works
        try:
            config.validate()
            print("⚠️  Configuration validated (but may be using placeholder values)")
        except ValueError as e:
            print(f"⚠️  Configuration validation failed (expected): {e}")
            print("   This is normal if you haven't set up your .env file yet")
        
        # Test username normalization
        username = config.get_target_username_normalized()
        print(f"✅ Target username: {username}")
        
        # Test moderation profile
        profile = config.get_moderation_profile()
        print(f"✅ Moderation profile: {profile['name']}")
        print(f"   Description: {profile['description']}")
        print(f"   Permissive mode: {profile.get('permissive_mode', False)}")
        if profile['behaviors']:
            print(f"   Monitoring {len(profile['behaviors'])} behavioral patterns")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_bot_modules() -> bool:
    """Test bot modules can be imported."""
    print("\nTesting bot modules...")
    
    try:
        from bot.filters import classify, ModerationResponse
        print("✅ Filters module imported successfully")
        print("✅ ModerationResponse class available")
        
        from bot.handlers import handle_message, handle_start, handle_status, handle_profile
        print("✅ Handlers module imported successfully")
        print("✅ All command handlers available")
        
        from bot.main import create_application
        print("✅ Main module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot modules test failed: {e}")
        return False


def test_moderation_system() -> bool:
    """Test the enhanced moderation system without API calls."""
    print("\nTesting moderation system...")
    
    try:
        from bot.filters import ModerationResponse, _build_system_prompt
        from config import config
        
        # Test ModerationResponse class
        response = ModerationResponse(
            allow=False,
            reason="Test message for validation",
            category="test"
        )
        
        response_dict = response.to_dict()
        expected_keys = {"allow", "reason", "category"}
        if set(response_dict.keys()) == expected_keys:
            print("✅ ModerationResponse class working correctly")
        else:
            print(f"❌ ModerationResponse missing keys: {expected_keys - set(response_dict.keys())}")
            return False
        
        # Test JSON parsing
        json_str = '{"allow": true, "reason": "Test reason", "category": "test"}'
        parsed_response = ModerationResponse.from_json(json_str)
        if parsed_response.allow and parsed_response.reason == "Test reason":
            print("✅ JSON parsing working correctly")
        else:
            print("❌ JSON parsing failed")
            return False
        
        # Test system prompt building
        try:
            prompt = _build_system_prompt()
            if "co-parenting" in prompt.lower() and "json" in prompt.lower():
                print("✅ System prompt generation working")
            else:
                print("❌ System prompt missing key elements")
                return False
        except Exception as e:
            print(f"❌ System prompt generation failed: {e}")
            return False
        
        # Test profile loading
        profile = config.get_moderation_profile()
        if profile and "name" in profile:
            print(f"✅ Moderation profile loaded: {profile['name']}")
        else:
            print("❌ Moderation profile loading failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Moderation system test failed: {e}")
        return False


def test_warning_system() -> bool:
    """Test the warning message building system."""
    print("\nTesting warning system...")
    
    try:
        from bot.handlers import _build_warning_message
        from bot.filters import ModerationResponse
        
        # Test different types of warning messages
        test_cases = [
            ("performative", "performative posturing"),
            ("manipulation", "emotional manipulation"),
            ("off_topic", "off-topic"),
        ]
        
        for category, expected_content in test_cases:
            response = ModerationResponse(
                allow=False,
                reason=f"Test {category} reason",
                category=category
            )
            
            warning = _build_warning_message(response)
            # Check that the warning contains both the base message and the reason
            if ("co-parenting logistics only" in warning.lower() and 
                f"test {category} reason" in warning.lower()):
                print(f"✅ Warning for '{category}' category working")
            else:
                print(f"❌ Warning for '{category}' category missing expected content")
                print(f"   Generated: {warning}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Warning system test failed: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print("🤖 Co-Parent Filter Bot - Enhanced Setup Test\n")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Project Structure", test_project_structure),
        ("Configuration & Profiles", test_configuration),
        ("Bot Modules", test_bot_modules),
        ("Moderation System", test_moderation_system),
        ("Warning System", test_warning_system),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your enhanced bot setup looks good.")
        print("\nNext steps:")
        print("1. Copy env.example to .env")
        print("2. Fill in your BOT_TOKEN and OPENAI_API_KEY")
        print("3. Set MODERATION_PROFILE (manipulative_coparent or standard)")
        print("4. Run: python -m bot.main")
        print("\n📋 Available commands in Telegram:")
        print("   /start - Show bot status")
        print("   /status - Detailed status")
        print("   /profile - Show moderation profile details")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 