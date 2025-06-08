from pymongo import MongoClient
import os
import datetime

def setup_database():
    """
    Set up the MongoDB database and collections for the Smart Construction Platform
    """
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        
        # Create or access the database
        db = client["construction_platform"]
        
        # Create collections if they don't exist
        if "video_data" not in db.list_collection_names():
            # Create video_data collection with validation
            db.create_collection("video_data")
            print("Created video_data collection")
            
            # Create indexes for better query performance
            db.video_data.create_index("timestamp")
            db.video_data.create_index("device_id")
            print("Created indexes for video_data collection")
        
        if "devices" not in db.list_collection_names():
            # Create devices collection
            db.create_collection("devices")
            print("Created devices collection")
            
            # Add sample device data
            db.devices.insert_one({
                "name": "Raspberry Pi Camera",
                "device_id": "raspberry_pi_1",
                "type": "camera",
                "location": "Main Construction Site",
                "ip_address": "192.168.3.7",
                "port": 5004,
                "status": "online",
                "last_connected": datetime.datetime.now()
            })
            print("Added sample device data")
            
            # Create index on device_id
            db.devices.create_index("device_id", unique=True)
            print("Created index for devices collection")
        
        # Create directories for storing video frames if they don't exist
        os.makedirs("../data/video_frames", exist_ok=True)
        print("Created directory for storing video frames")
        
        print("Database setup completed successfully.")
        return True
    
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    setup_database() 