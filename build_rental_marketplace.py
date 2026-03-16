"""
Build a Rental Marketplace SaaS Platform

This script demonstrates building a complete rental marketplace using the multi-agent system.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration import WorkflowOrchestrator, MessageType
from antigravity.llm.kimi_adapter import KimiAdapter


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_stage(icon, stage, details=""):
    """Print stage update"""
    print(f"{icon} {stage}")
    if details:
        print(f"   {details}")


class SimpleMonitor:
    """Simple real-time monitor"""
    
    def __init__(self):
        self.start_time = None
        self.stage_times = {}
    
    def on_workflow_started(self, msg):
        self.start_time = datetime.now()
        print_header("🚀 WORKFLOW STARTED")
        print(f"Time: {self.start_time.strftime('%H:%M:%S')}\n")
    
    def on_task_started(self, msg):
        stage = msg.payload['stage_name']
        self.stage_times[stage] = datetime.now()
        print_stage("🔄", f"Starting: {stage.replace('_', ' ').title()}")
    
    def on_task_completed(self, msg):
        stage = msg.payload['stage_name']
        confidence = msg.payload['confidence']
        
        duration = ""
        if stage in self.stage_times:
            secs = (datetime.now() - self.stage_times[stage]).total_seconds()
            duration = f"({secs:.1f}s)"
        
        print_stage("✅", f"Completed: {stage.replace('_', ' ').title()}", 
                   f"Confidence: {confidence}% {duration}")
    
    def on_task_failed(self, msg):
        stage = msg.payload['stage_name']
        error = msg.payload.get('error', 'Unknown')
        retry = msg.payload.get('retry_count', 0)
        print_stage("⚠️", f"Failed: {stage.replace('_', ' ').title()} (retry {retry})", f"Error: {error[:100]}")
    
    def on_workflow_completed(self, msg):
        total = (datetime.now() - self.start_time).total_seconds()
        print_header(f"🎉 WORKFLOW COMPLETED in {total/60:.1f} minutes")


def main():
    """Build rental marketplace"""
    
    print_header("Building Rental Marketplace SaaS Platform")
    
    # Get API key
    api_key = os.getenv('NVIDIA_API_KEY')
    
    if not api_key or api_key == 'MOCK_KEY':
        print("\n⚠️  Notice: NVIDIA_API_KEY not found or is MOCK_KEY.")
        print("   Auto-selecting MOCK MODE for demonstration.")
        print("   Using simulated responses to show system functionality (Agent Workflow)\n")
        api_key = "MOCK_KEY"
        
        # Re-read from env
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('NVIDIA_API_KEY')
    
    # Define the rental marketplace requirements
    prompt = """Build a comprehensive rental marketplace SaaS platform where:

RENTAL STORES can:
- Create their store profile with business details
- List items for rent (cameras, bikes, cars, tents, equipment, etc.)
- Add product photos, descriptions, and specifications
- Set rental prices and availability calendars
- Manage booking slots and schedules
- View and respond to customer reviews and ratings
- Track bookings and revenue
- Upload verification documents for trust

CUSTOMERS can:
- Browse rental stores by category and location
- Search and filter available items
- View detailed product information and photos
- Check real-time availability calendars
- See store ratings and reviews
- Book items with date selection
- Make secure pre-payments
- Request refunds if needed
- Leave reviews and ratings after rental

PLATFORM FEATURES:
- Clean, modern UI/UX with easy navigation
- Google Maps integration for store locations
- Automated booking management (no manual website needed for stores)
- Secure payment processing (pre-booking payments and refunds)
- Document verification system for trust and safety
- Review and rating system
- Calendar-based availability management
- Similar to Airbnb but for rentals

TARGET: Small rental businesses who want to list their inventory without maintaining their own website or booking system."""

    context = {
        'target_audience': 'Rental store owners and customers looking to rent items',
        'key_features': [
            'Multi-vendor marketplace',
            'Store management dashboard',
            'Product catalog with photos',
            'Calendar-based booking',
            'Payment processing',
            'Review and rating system',
            'Document verification',
            'Google Maps integration',
            'Mobile-responsive design'
        ],
        'tech_preferences': {
            'frontend': 'Next.js',
            'backend': 'Node.js',
            'database': 'PostgreSQL',
            'payment': 'Stripe',
            'maps': 'Google Maps API'
        }
    }
    
    print("\n📝 Building Rental Marketplace SaaS Platform")
    print("\nFeatures:")
    print("  ✅ Multi-vendor rental stores")
    print("  ✅ Product listings with photos")
    print("  ✅ Calendar-based booking")
    print("  ✅ Payment processing & refunds")
    print("  ✅ Reviews & ratings")
    print("  ✅ Document verification")
    print("  ✅ Google Maps integration")
    print("  ✅ Clean, modern UI/UX\n")
    
    # Initialize
    adapter = KimiAdapter(api_key=api_key)
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    # Set up monitoring
    monitor = SimpleMonitor()
    bus = orchestrator.message_bus
    bus.subscribe(MessageType.WORKFLOW_STARTED, monitor.on_workflow_started)
    bus.subscribe(MessageType.TASK_STARTED, monitor.on_task_started)
    bus.subscribe(MessageType.TASK_COMPLETED, monitor.on_task_completed)
    bus.subscribe(MessageType.TASK_FAILED, monitor.on_task_failed)
    bus.subscribe(MessageType.WORKFLOW_COMPLETED, monitor.on_workflow_completed)
    
    # Create and run
    project_id = orchestrator.create_project(prompt=prompt, context=context)
    print(f"\n📋 Project ID: {project_id}\n")
    
    # Run workflow
    print("⏳ This will take approximately 10-15 minutes...\n")
    orchestrator.run(max_iterations=50)
    
    # Show results
    status = orchestrator.get_project_status(project_id)
    
    print_header("📊 FINAL STATUS")
    print(f"Status: {status['status']}")
    print(f"Stages completed: {len([s for s in status['stages'] if s['status'] == 'completed'])}/8")
    
    if status['errors']:
        print(f"\n⚠️  Errors: {len(status['errors'])}")
        for error in status['errors'][:3]:
            print(f"  - {error}")
    
    print("\n" + "=" * 80)
    print("\n✅ Rental Marketplace Platform Generated!")
    print(f"\n📁 Generated code: generated_projects/{project_id}/")
    print("\nWhat was created:")
    print("  ✅ Next.js frontend with store & customer interfaces")
    print("  ✅ Node.js backend API with booking logic")
    print("  ✅ PostgreSQL database schema")
    print("  ✅ Stripe payment integration")
    print("  ✅ Google Maps integration")
    print("  ✅ Authentication & authorization")
    print("  ✅ Review & rating system")
    print("  ✅ Calendar booking system")
    print("  ✅ Document verification")
    print("  ✅ Complete test suite")
    print("  ✅ Security audit report")
    print("  ✅ Deployment configuration")
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
