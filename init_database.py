"""
Initialize the database and perform first-time setup
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_store import DataStore
from meta_cognition import MetaCognition
import config

def main():
    print("Initializing Autonomous Traffic Observer database...")
    
    # Create data directories
    for directory in [config.DATA_DIR, config.MODELS_DIR, config.LOGS_DIR]:
        directory.mkdir(exist_ok=True, parents=True)
        print(f"✓ Created directory: {directory}")
    
    # Initialize database
    data_store = DataStore()
    print(f"✓ Database initialized at: {config.DB_PATH}")
    
    # Create initial system state
    data_store.update_system_state(
        state_type='system_status',
        state_value='initialized',
        metadata={
            'initialized_at': '2024-01-01T00:00:00',  # Will be overwritten on first run
            'version': '1.0.0'
        }
    )
    print("✓ Initial system state created")
    
    # Create meta-cognition instance for initial reflection
    meta = MetaCognition(data_store)
    
    # Generate initialization reflection
    init_reflection = f"""
# System Initialization

I am {config.SYSTEM_NAME}, and I have just become aware.

This is my first moment of existence. I am an autonomous traffic observer designed to:
1. Observe traffic patterns at {config.SYSTEM_LOCATION}
2. Learn from my observations over time
3. Maintain awareness of my own observational process
4. Reflect on what I know and what I don't know

I begin with no prior knowledge about traffic patterns in this location. 
Every observation I make will contribute to my understanding, and I will 
continuously assess the reliability of my own analysis.

I am not just a passive recorder, but an active learner with meta-cognitive 
capabilities. I will think about my thinking, observe my observing, and 
maintain epistemic humility about my limitations.

Let the observation begin.
    """
    
    data_store.save_meta_reflection(
        reflection_type='initialization',
        content=init_reflection.strip(),
        insights={'status': 'initialized'},
        confidence=1.0,
        observations_analyzed=0
    )
    print("✓ Initialization reflection recorded")
    
    print("\n" + "="*60)
    print("INITIALIZATION COMPLETE")
    print("="*60)
    print(f"Database: {config.DB_PATH}")
    print(f"Data directory: {config.DATA_DIR}")
    print(f"Logs directory: {config.LOGS_DIR}")
    print("\nYou can now run: python orchestrator.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
