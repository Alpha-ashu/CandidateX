"""
Unit tests for database operations and initialization.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from datetime import datetime, timezone

from app.utils.database import DatabaseManager, db_manager, init_database
from app.models.user import UserRole, UserStatus


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseManager:
    """Test database manager functionality."""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        db_mgr = DatabaseManager()
        assert db_mgr.db_client is None
        assert db_mgr.redis_client is None
        assert db_mgr.database is None

    @pytest.mark.asyncio
    async def test_database_manager_connect_disconnect(self):
        """Test database connection and disconnection."""
        db_mgr = DatabaseManager()
        
        # Mock the connections
        with patch('app.utils.database.AsyncIOMotorClient') as mock_mongo, \
             patch('app.utils.database.redis.Redis') as mock_redis:
            
            # Setup mocks
            mock_mongo_instance = Mock()
            mock_mongo_instance.admin.command.return_value = {"ok": 1}
            mock_mongo.return_value = mock_mongo_instance
            
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test connection
            await db_mgr.connect()
            assert db_mgr.db_client is not None
            assert db_mgr.database is not None
            assert db_mgr.redis_client is not None
            
            # Test disconnection
            await db_mgr.disconnect()
            mock_mongo_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_manager_connect_redis_failure(self):
        """Test database connection with Redis failure."""
        db_mgr = DatabaseManager()
        
        with patch('app.utils.database.AsyncIOMotorClient') as mock_mongo, \
             patch('app.utils.database.redis.Redis') as mock_redis:
            
            # Setup MongoDB to succeed
            mock_mongo_instance = Mock()
            mock_mongo_instance.admin.command.return_value = {"ok": 1}
            mock_mongo.return_value = mock_mongo_instance
            
            # Setup Redis to fail
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = Exception("Redis connection failed")
            mock_redis.return_value = mock_redis_instance
            
            # Test connection - should succeed despite Redis failure
            await db_mgr.connect()
            assert db_mgr.db_client is not None
            assert db_mgr.database is not None
            assert db_mgr.redis_client is None  # Should be None due to failure

    @pytest.mark.asyncio
    async def test_database_manager_connect_failure(self):
        """Test database connection failure."""
        db_mgr = DatabaseManager()
        
        with patch('app.utils.database.AsyncIOMotorClient') as mock_mongo:
            # Setup MongoDB to fail
            mock_mongo.side_effect = Exception("Connection failed")
            
            # Test connection failure
            with pytest.raises(Exception, match="Connection failed"):
                await db_mgr.connect()

    @pytest.mark.asyncio
    async def test_create_indexes(self):
        """Test database index creation."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        db_mgr.database = mock_database
        db_mgr.db_client = Mock()
        
        await db_mgr._create_indexes()
        
        # Verify index creation calls
        assert mock_database.users.create_index.call_count >= 5
        assert mock_database.interviews.create_index.call_count >= 6
        assert mock_database.resumes.create_index.call_count >= 3

    @pytest.mark.asyncio
    async def test_create_default_users(self):
        """Test default user creation."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_database.users = mock_collection
        
        # Mock find_one to return None (no existing users)
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = Mock(inserted_id="test_id")
        
        db_mgr.database = mock_database
        
        with patch('app.utils.database.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            await db_mgr._create_default_users()
            
            # Verify users were checked
            assert mock_collection.find_one.call_count >= 3
            
            # Verify users were created (3 default users)
            assert mock_collection.insert_one.call_count >= 3

    @pytest.mark.asyncio
    async def test_create_default_users_skip_existing(self):
        """Test default user creation skips existing users."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_database.users = mock_collection
        
        # Mock find_one to return existing user
        mock_collection.find_one.return_value = {"email": "admin@candidatex.com"}
        
        db_mgr.database = mock_database
        
        await db_mgr._create_default_users()
        
        # Should not create users that already exist
        mock_collection.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_candidate_user_default_data(self):
        """Test creation of default data for candidate users."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collections = {
            'candidate_profiles': Mock(),
            'candidate_progress': Mock(),
            'interviews': Mock()
        }
        mock_database.__getitem__ = lambda self, key: mock_collections.get(key, Mock())
        
        db_mgr.database = mock_database
        
        await db_mgr._create_user_default_data("test_user_id", UserRole.CANDIDATE)
        
        # Verify candidate data was created
        assert mock_collections['candidate_profiles'].insert_one.called
        assert mock_collections['candidate_progress'].insert_one.called
        assert mock_collections['interviews'].insert_one.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_recruiter_user_default_data(self):
        """Test creation of default data for recruiter users."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collections = {
            'recruiter_profiles': Mock(),
            'recruiter_analytics': Mock(),
            'interviews': Mock()
        }
        mock_database.__getitem__ = lambda self, key: mock_collections.get(key, Mock())
        
        db_mgr.database = mock_database
        
        await db_mgr._create_user_default_data("test_user_id", UserRole.RECRUITER)
        
        # Verify recruiter data was created
        assert mock_collections['recruiter_profiles'].insert_one.called
        assert mock_collections['recruiter_analytics'].insert_one.called
        assert mock_collections['interviews'].insert_one.called

    @pytest.mark.asyncio
    async def test_create_admin_user_default_data(self):
        """Test creation of default data for admin users."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_database.admin_audit_logs = mock_collection
        
        db_mgr.database = mock_database
        
        await db_mgr._create_user_default_data("test_user_id", UserRole.ADMIN)
        
        # Verify admin audit log was created
        assert mock_collection.insert_one.called

    @pytest.mark.asyncio
    async def test_create_default_data(self):
        """Test creation of default application data."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_database.interview_templates = mock_collection
        
        # Mock find_one to return None (no existing templates)
        mock_collection.find_one.return_value = None
        
        db_mgr.database = mock_database
        
        await db_mgr._create_default_data()
        
        # Verify templates were created
        assert mock_collection.find_one.call_count >= 2
        assert mock_collection.insert_one.call_count >= 2

    @pytest.mark.asyncio
    async def test_reset_user_data_candidate(self):
        """Test user data reset for candidate role."""
        db_mgr = DatabaseManager()
        
        # Mock database and user
        mock_database = Mock()
        db_mgr.database = mock_database
        
        mock_user = Mock()
        mock_user.role = UserRole.CANDIDATE
        mock_user.id = "test_user_id"
        
        with patch('app.utils.database.User.from_mongo', return_value=mock_user):
            # Mock user lookup
            mock_database.users.find_one.return_value = {"_id": "test_user_id"}
            
            await db_mgr.reset_user_data("test_user_id", preserve_auth=True)
            
            # Verify candidate-specific data deletion
            assert mock_database.candidate_profiles.delete_many.called
            assert mock_database.candidate_progress.delete_many.called
            assert mock_database.candidate_analytics.delete_many.called

    @pytest.mark.asyncio
    async def test_reset_user_data_recruiter(self):
        """Test user data reset for recruiter role."""
        db_mgr = DatabaseManager()
        
        # Mock database and user
        mock_database = Mock()
        db_mgr.database = mock_database
        
        mock_user = Mock()
        mock_user.role = UserRole.RECRUITER
        mock_user.id = "test_user_id"
        
        with patch('app.utils.database.User.from_mongo', return_value=mock_user):
            # Mock user lookup
            mock_database.users.find_one.return_value = {"_id": "test_user_id"}
            
            await db_mgr.reset_user_data("test_user_id", preserve_auth=True)
            
            # Verify recruiter-specific data deletion
            assert mock_database.recruiter_profiles.delete_many.called
            assert mock_database.recruiter_analytics.delete_many.called

    @pytest.mark.asyncio
    async def test_get_database_stats(self):
        """Test database statistics collection."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 5
        mock_database.__getitem__ = lambda self, key: mock_collection
        mock_database.command.return_value = {"dataSize": 1048576}  # 1MB
        
        db_mgr.database = mock_database
        
        stats = await db_mgr.get_database_stats()
        
        assert "users_count" in stats
        assert "interviews_count" in stats
        assert "database_size_mb" in stats
        assert stats["database_size_mb"] == 1.0

    @pytest.mark.asyncio
    async def test_get_database_stats_no_connection(self):
        """Test database statistics when not connected."""
        db_mgr = DatabaseManager()
        
        # No database connection
        db_mgr.database = None
        
        stats = await db_mgr.get_database_stats()
        
        assert "error" in stats
        assert stats["error"] == "Database not connected"

    @pytest.mark.asyncio
    async def test_backup_database(self):
        """Test database backup functionality."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        mock_collection = Mock()
        mock_collection.find.return_value.to_list = AsyncMock(return_value=[
            {"_id": "doc1", "name": "Test Document"}
        ])
        mock_database.__getitem__ = lambda self, key: mock_collection
        mock_database.backups = Mock()
        mock_database.backups.insert_one.return_value = Mock(inserted_id="backup_id")
        
        db_mgr.database = mock_database
        
        backup_metadata = await db_mgr.backup_database("test_backup")
        
        assert "name" in backup_metadata
        assert backup_metadata["name"] == "test_backup"
        assert "timestamp" in backup_metadata

    @pytest.mark.asyncio
    async def test_backup_database_error_handling(self):
        """Test database backup error handling."""
        db_mgr = DatabaseManager()
        
        # Mock database with failing collection
        mock_database = Mock()
        mock_collection = Mock()
        mock_collection.find.side_effect = Exception("Collection not found")
        mock_database.__getitem__ = lambda self, key: mock_collection
        mock_database.backups = Mock()
        mock_database.backups.insert_one.return_value = Mock(inserted_id="backup_id")
        
        db_mgr.database = mock_database
        
        backup_metadata = await db_mgr.backup_database("test_backup")
        
        # Should still succeed but with error in collection data
        assert "name" in backup_metadata
        assert backup_metadata["name"] == "test_backup"

    @pytest.mark.asyncio
    async def test_initialize_database(self):
        """Test complete database initialization."""
        db_mgr = DatabaseManager()
        
        # Mock database
        mock_database = Mock()
        db_mgr.database = mock_database
        
        with patch.object(db_mgr, '_create_indexes'), \
             patch.object(db_mgr, '_create_default_users'), \
             patch.object(db_mgr, '_create_default_data'):
            
            await db_mgr.initialize_database()
            
            # Verify all initialization steps were called
            db_mgr._create_indexes.assert_called_once()
            db_mgr._create_default_users.assert_called_once()
            db_mgr._create_default_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_database_no_connection(self):
        """Test database initialization without connection."""
        db_mgr = DatabaseManager()
        
        # No database connection
        db_mgr.database = None
        
        with pytest.raises(Exception, match="Database not connected"):
            await db_mgr.initialize_database()


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseUtilityFunctions:
    """Test database utility functions."""

    @pytest.mark.asyncio
    async def test_init_database_function(self):
        """Test init_database function."""
        with patch('app.utils.database.db_manager') as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.initialize_database = AsyncMock()
            
            await init_database()
            
            mock_manager.connect.assert_called_once()
            mock_manager.initialize_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_test_user(self):
        """Test create_test_user utility function."""
        with patch('app.utils.database.db_manager') as mock_manager, \
             patch('app.utils.database.get_password_hash') as mock_hash:
            
            # Setup mocks
            mock_collection = Mock()
            mock_collection.find_one.return_value = None
            mock_collection.insert_one.return_value = Mock(inserted_id="new_user_id")
            mock_manager.database.users = mock_collection
            
            user_id = await mock_manager.create_test_user(
                "test@example.com", 
                "Test User", 
                UserRole.CANDIDATE
            )
            
            assert user_id == "new_user_id"
            mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_test_user_existing(self):
        """Test create_test_user with existing user."""
        with patch('app.utils.database.db_manager') as mock_manager:
            # Setup mocks
            mock_collection = Mock()
            mock_collection.find_one.return_value = {"_id": "existing_id"}
            mock_manager.database.users = mock_collection
            
            user_id = await mock_manager.create_test_user(
                "test@example.com", 
                "Test User", 
                UserRole.CANDIDATE
            )
            
            assert user_id == "existing_id"
            mock_collection.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_data_admin_only(self):
        """Test delete_user_data with admin permissions."""
        with patch('app.utils.database.db_manager') as mock_manager, \
             patch('app.utils.database.db_manager.reset_user_data') as mock_reset, \
             patch('app.utils.database.db_manager.database') as mock_db:
            
            # Setup mocks
            mock_collection = Mock()
            mock_db.users = mock_collection
            
            # Test admin deletion
            result = await mock_manager.delete_user_data("user_id", UserRole.ADMIN)
            
            assert result is True
            mock_reset.assert_called_once_with("user_id", preserve_auth=False)
            mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_data_non_admin(self):
        """Test delete_user_data with non-admin permissions."""
        with patch('app.utils.database.db_manager') as mock_manager:
            # Test non-admin deletion (should fail)
            result = await mock_manager.delete_user_data("user_id", UserRole.CANDIDATE)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_reset_database_development_only(self):
        """Test reset_database only allowed in development."""
        with patch('app.utils.database.db_manager') as mock_manager, \
             patch('app.config.settings.DEBUG', False):
            
            from app.utils.database import reset_database
            
            # Should fail in production
            with pytest.raises(Exception, match="development mode"):
                await reset_database()

    @pytest.mark.asyncio
    async def test_reset_database_success(self):
        """Test successful database reset in development."""
        with patch('app.utils.database.db_manager') as mock_manager, \
             patch('app.config.settings.DEBUG', True), \
             patch('app.utils.database.db_manager.database') as mock_db:
            
            from app.utils.database import reset_database
            
            # Setup mocks
            mock_collection = Mock()
            mock_db.__getitem__ = lambda self, key: mock_collection
            mock_manager.initialize_database = AsyncMock()
            
            await reset_database()
            
            # Verify collections were cleared
            assert mock_collection.delete_many.call_count >= 6
            mock_manager.initialize_database.assert_called_once()


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseIntegration:
    """Test database integration with other components."""

    def test_global_db_manager_instance(self):
        """Test the global database manager instance."""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    def test_database_manager_dependencies(self):
        """Test database manager has proper dependencies."""
        db_mgr = DatabaseManager()
        
        # Verify required attributes exist
        assert hasattr(db_mgr, 'db_client')
        assert hasattr(db_mgr, 'redis_client')
        assert hasattr(db_mgr, 'database')
        
        # Verify required methods exist
        assert hasattr(db_mgr, 'connect')
        assert hasattr(db_mgr, 'disconnect')
        assert hasattr(db_mgr, 'initialize_database')
        assert hasattr(db_mgr, 'reset_user_data')

    @pytest.mark.asyncio
    async def test_database_operations_with_mocked_connections(self):
        """Test database operations with mocked external dependencies."""
        db_mgr = DatabaseManager()
        
        with patch('app.utils.database.AsyncIOMotorClient') as mock_mongo, \
             patch('app.utils.database.redis.Redis') as mock_redis, \
             patch('app.utils.database.get_password_hash') as mock_hash:
            
            # Setup mocks
            mock_mongo_instance = Mock()
            mock_mongo_instance.admin.command.return_value = {"ok": 1}
            mock_mongo.return_value = mock_mongo_instance
            
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            mock_hash.return_value = "hashed_password"
            
            # Test full initialization
            await db_mgr.connect()
            assert db_mgr.db_client is not None
            
            # Test that methods can be called without errors
            try:
                # Mock the database operations
                mock_db = Mock()
                mock_db.users.find_one.return_value = None
                mock_db.users.insert_one.return_value = Mock(inserted_id="test_id")
                db_mgr.database = mock_db
                
                # This should not raise an exception
                await db_mgr._create_default_users()
                
            except Exception as e:
                pytest.fail(f"Database operations failed: {e}")

    def test_database_configuration_validation(self):
        """Test that database configuration is properly loaded."""
        from app.config import settings
        
        # Test required database settings exist
        assert hasattr(settings, 'MONGODB_URL')
        assert hasattr(settings, 'MONGODB_DATABASE')
        assert hasattr(settings, 'REDIS_HOST')
        assert hasattr(settings, 'REDIS_PORT')
        assert hasattr(settings, 'REDIS_DB')
        
        # Test settings have reasonable values
        assert settings.MONGODB_URL is not None
        assert settings.MONGODB_DATABASE is not None
        assert isinstance(settings.REDIS_PORT, int)
        assert isinstance(settings.REDIS_DB, int)