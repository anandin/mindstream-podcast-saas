#!/usr/bin/env python3
"""
Test suite for SaaS Podcast Generator.
"""
import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_saas.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from saas.db.models import (
    Base, User, Podcast, Episode, APIKey, UsageLog, SubscriptionTier,
    check_user_limit, SUBSCRIPTION_LIMITS, init_db
)
from saas.db import get_db
from sqlalchemy import func
from saas.auth.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, generate_api_key, hash_api_key, verify_api_key
)


def setup_test_db():
    """Setup test database."""
    # Remove old test db if exists
    if os.path.exists("./test_saas.db"):
        os.remove("./test_saas.db")
    
    init_db(TEST_DATABASE_URL)
    print("✓ Test database initialized")


def test_user_registration():
    """Test user registration."""
    print("\n=== Testing User Registration ===")
    
    # Test password hashing
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("wrongpassword", hashed), "Wrong password should fail"
    print("✓ Password hashing works")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Create user
        user = User(
            email="test@example.com",
            password_hash=hashed,
            name="Test User",
            company="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
        )
        db.add(user)
        db.commit()
        
        # Verify user was created
        db.refresh(user)
        assert user.id is not None, "User ID should be set"
        assert user.email == "test@example.com", "Email should match"
        print(f"✓ User created with ID: {user.id}")
        
        # Store user ID for later tests
        user_id = user.id
        user_email = user.email
    
    return {"id": user_id, "email": user_email}


def test_authentication(user_data):
    """Test authentication."""
    print("\n=== Testing Authentication ===")
    
    # Create access token
    access_token = create_access_token({"user_id": user_data["id"], "email": user_data["email"]})
    assert access_token is not None, "Access token should be created"
    print("✓ Access token created")
    
    # Create refresh token
    refresh_token = create_refresh_token({"user_id": user_data["id"], "email": user_data["email"]})
    assert refresh_token is not None, "Refresh token should be created"
    print("✓ Refresh token created")
    
    # Decode tokens
    payload = decode_token(access_token)
    assert payload is not None, "Token should decode successfully"
    assert payload["user_id"] == user_data["id"], "User ID should match"
    assert payload["type"] == "access", "Token type should be access"
    print("✓ Token decoding works")
    
    # Test invalid token
    assert decode_token("invalid_token") is None, "Invalid token should return None"
    print("✓ Invalid token handling works")


def test_api_keys(user_data):
    """Test API key generation and verification."""
    print("\n=== Testing API Keys ===")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Generate API key
        full_key, key_hash, prefix = generate_api_key()
        assert full_key.startswith("mtg_"), "API key should start with mtg_"
        assert len(full_key) > 20, "API key should be sufficiently long"
        print(f"✓ API key generated: {prefix}****")
        
        # Store API key
        api_key = APIKey(
            user_id=user_data["id"],
            key_hash=key_hash,
            prefix=prefix,
            name="Test API Key",
            rate_limit_per_hour=100,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        # Verify API key
        assert verify_api_key(full_key, key_hash), "API key verification failed"
        assert not verify_api_key("wrong_key", key_hash), "Wrong key should fail"
        print("✓ API key verification works")
        
        return api_key


def test_subscription_limits():
    """Test subscription tier limits."""
    print("\n=== Testing Subscription Limits ===")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Get free user
        user = db.query(User).first()
        
        # Test free tier limits
        limits = SUBSCRIPTION_LIMITS[SubscriptionTier.FREE]
        assert limits["episodes_per_month"] == 3, "Free tier should have 3 episodes"
        assert limits["api_calls_per_month"] == 100, "Free tier should have 100 API calls"
        assert limits["storage_mb"] == 100, "Free tier should have 100MB storage"
        print("✓ Free tier limits verified")
        
        # Test limit checking
        user.episodes_generated_this_month = 3
        can_proceed, message = check_user_limit(user, "episodes")
        assert not can_proceed, "Should not be able to generate more episodes"
        print(f"✓ Limit check works: {message}")
        
        # Reset and check again
        user.episodes_generated_this_month = 0
        can_proceed, message = check_user_limit(user, "episodes")
        assert can_proceed, "Should be able to generate episodes"
        print("✓ Limit reset works")


def test_podcast_crud(user_data):
    """Test podcast CRUD operations."""
    print("\n=== Testing Podcast CRUD ===")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Create podcast
        podcast = Podcast(
            user_id=user_data["id"],
            title="Test Podcast",
            description="A test podcast",
            language="en",
            host_1_name="Alex",
            host_2_name="Maya",
            tts_provider="elevenlabs",
            target_word_count=1500,
        )
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
        
        assert podcast.id is not None, "Podcast ID should be set"
        assert podcast.title == "Test Podcast", "Title should match"
        print(f"✓ Podcast created with ID: {podcast.id}")
        
        # Update podcast
        podcast.title = "Updated Podcast"
        db.commit()
        db.refresh(podcast)
        assert podcast.title == "Updated Podcast", "Title should be updated"
        print("✓ Podcast updated")
        
        # List podcasts (multi-tenancy test)
        podcasts = db.query(Podcast).filter(Podcast.user_id == user_data["id"]).all()
        assert len(podcasts) == 1, "Should have 1 podcast"
        print("✓ Podcast listing works")
        
        # Delete podcast (soft delete)
        podcast.is_active = False
        db.commit()
        podcasts = db.query(Podcast).filter(Podcast.user_id == user_data["id"], Podcast.is_active == True).all()
        assert len(podcasts) == 0, "Should have 0 active podcasts"
        print("✓ Podcast deletion (soft) works")
        
        return {"id": podcast.id, "user_id": user_data["id"]}


def test_episode_crud(user_data, podcast_data):
    """Test episode CRUD operations."""
    print("\n=== Testing Episode CRUD ===")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Reactivate podcast for testing
        podcast = db.query(Podcast).filter(Podcast.id == podcast_data["id"]).first()
        podcast.is_active = True
        db.commit()
        
        # Create episode
        episode = Episode(
            podcast_id=podcast.id,
            date=datetime.now(timezone.utc),
            title="Test Episode",
            status="draft",
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)
        
        assert episode.id is not None, "Episode ID should be set"
        print(f"✓ Episode created with ID: {episode.id}")
        
        # Update episode
        episode.status = "ready"
        episode.audio_duration_seconds = 300.5
        db.commit()
        db.refresh(episode)
        
        assert episode.status == "ready", "Status should be updated"
        print("✓ Episode updated")
        
        # List episodes
        episodes = db.query(Episode).filter(Episode.podcast_id == podcast.id).all()
        assert len(episodes) == 1, "Should have 1 episode"
        print("✓ Episode listing works")
        
        # Test multi-tenancy isolation
        # Create another user with their own podcast
        other_user = User(
            email="other@example.com",
            password_hash=hash_password("password"),
            subscription_tier=SubscriptionTier.FREE,
        )
        db.add(other_user)
        db.commit()
        
        other_podcast = Podcast(
            user_id=other_user.id,
            title="Other Podcast",
            is_active=True,
        )
        db.add(other_podcast)
        db.commit()
        
        # Verify data isolation
        user_podcasts = db.query(Podcast).filter(Podcast.user_id == user_data["id"], Podcast.is_active == True).all()
        other_podcasts = db.query(Podcast).filter(Podcast.user_id == other_user.id, Podcast.is_active == True).all()
        
        assert len(user_podcasts) == 1, "User should have 1 podcast"
        assert len(other_podcasts) == 1, "Other user should have 1 podcast"
        assert user_podcasts[0].title != other_podcasts[0].title, "Podcasts should be different"
        print("✓ Multi-tenancy isolation verified")


def test_usage_logging(user_data, podcast_data):
    """Test usage logging."""
    print("\n=== Testing Usage Logging ===")
    
    with get_db(TEST_DATABASE_URL) as db:
        # Log episode generation
        log = UsageLog(
            user_id=user_data["id"],
            podcast_id=podcast_data["id"],
            action="episode_generation",
            tokens_used=5000,
            cost_usd=0.15,
        )
        db.add(log)
        db.commit()
        
        assert log.id is not None, "Log ID should be set"
        print("✓ Usage log created")
        
        # Query usage
        total_cost = db.query(UsageLog).filter(
            UsageLog.user_id == user_data["id"],
            UsageLog.action == "episode_generation"
        ).with_entities(func.sum(UsageLog.cost_usd)).scalar()
        
        assert total_cost == 0.15, "Total cost should match"
        print("✓ Usage aggregation works")


def cleanup():
    """Cleanup test database."""
    if os.path.exists("./test_saas.db"):
        os.remove("./test_saas.db")
    print("\n✓ Test database cleaned up")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("SaaS Podcast Generator - Test Suite")
    print("=" * 60)
    
    try:
        setup_test_db()
        
        # Run tests
        user_data = test_user_registration()
        test_authentication(user_data)
        test_api_keys(user_data)
        test_subscription_limits()
        podcast_data = test_podcast_crud(user_data)
        test_episode_crud(user_data, podcast_data)
        test_usage_logging(user_data, podcast_data)
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        cleanup()
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
