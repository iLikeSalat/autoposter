"""
AutoPoster - Production-ready automated social media posting system.

Main entry point for the application.
"""
import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.logger import setup_logger
from src.autoposter import AutoPoster


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AutoPoster - Automated social media posting system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run in normal mode (scheduled posting)
  python main.py --test             # Test both text and image posts
  python main.py --test-text        # Test only text post
  python main.py --test-image       # Test only image post
  python main.py --test-replies     # Test auto-reply system
  python main.py --config custom.yaml  # Use custom config file
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (test both text and image posts, then exit)'
    )
    parser.add_argument(
        '--test-text',
        action='store_true',
        help='Test only text post'
    )
    parser.add_argument(
        '--test-image',
        action='store_true',
        help='Test only image post'
    )
    parser.add_argument(
        '--test-replies',
        action='store_true',
        help='Test auto-reply system (process one reply and exit)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger(log_level=args.log_level)
    
    try:
        # Load configuration
        config = Config(config_path=args.config)
        logger.info(f"Configuration loaded from {args.config}")
        
        # Initialize AutoPoster
        poster = AutoPoster(config=config, logger=logger)
        
        # Verify credentials
        logger.info("Verifying platform credentials...")
        if poster.enable_threads and poster.threads_poster:
            if not poster.threads_poster.verify_credentials():
                logger.error("Threads authentication failed. Please check your credentials.")
                return 1
        
        enabled_platforms = []
        if poster.enable_threads:
            enabled_platforms.append('Threads')
        if poster.enable_twitter:
            enabled_platforms.append('Twitter')
        
        logger.info(f"Enabled platforms: {', '.join(enabled_platforms)}")
        
        # Handle different test modes
        if args.test_text:
            logger.info("Running in TEST MODE - Text Post Only")
            success = poster.post_thread(post_type='text')
            if success:
                logger.info("✅ Text post test: SUCCESS")
            else:
                logger.error("❌ Text post test: FAILED")
                return 1
                
        elif args.test_image:
            logger.info("Running in TEST MODE - Image Post Only")
            success = poster.post_thread(post_type='image')
            if success:
                logger.info("✅ Image post test: SUCCESS")
            else:
                logger.error("❌ Image post test: FAILED")
                return 1
                
        elif args.test:
            logger.info("Running in TEST MODE - Both Text and Image Posts")
            success_text = poster.post_thread(post_type='text')
            if success_text:
                logger.info("✅ Text post test: SUCCESS")
            else:
                logger.error("❌ Text post test: FAILED")
            
            import time
            logger.info("Waiting 5 seconds before image test...")
            time.sleep(5)
            
            success_image = poster.post_thread(post_type='image')
            if success_image:
                logger.info("✅ Image post test: SUCCESS")
            else:
                logger.error("❌ Image post test: FAILED")
            
            if success_text and success_image:
                logger.info("🎉 All tests passed!")
                return 0
            else:
                logger.warning("⚠️  Partial success. Check the errors above.")
                return 1
                
        elif args.test_replies:
            logger.info("Running in TEST MODE - Auto-Reply System")
            if not poster.enable_auto_replies:
                logger.error("Auto-replies are not enabled!")
                logger.error("Set ENABLE_AUTO_REPLIES=true in .env or enable_auto_replies: true in config.yaml")
                return 1
            
            if not poster.reply_manager or not poster.reply_generator:
                logger.error("Reply system not initialized")
                return 1
            
            poster._process_replies()
            logger.info("✅ Reply test complete")
            
        else:
            # Normal mode - run continuously
            logger.info("Starting AutoPoster in normal mode...")
            poster.run()
            
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
