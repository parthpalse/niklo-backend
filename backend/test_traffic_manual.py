from services.traffic_service import TrafficService
import os

def test_traffic():
    print("Testing Google Maps Traffic Service...")
    
    # Hardcoded test case: Thane home to Dadar
    origin = "Thane West, Maharashtra, India"
    destination = "Dadar, Mumbai, Maharashtra, India"
    
    # Check if API Key is set
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        print("ERROR: GOOGLE_MAPS_API_KEY is not set in environment or .env file.")
        print("Please set it in backend/.env")
        return

    service = TrafficService()
    result = service.get_travel_time(origin, destination)
    
    if 'error' in result:
        print(f"FAILED: {result['error']}")
    else:
        print("SUCCESS!")
        print(f"From: {origin}")
        print(f"To: {destination}")
        print(f"Distance: {result['distance_text']}")
        print(f"Duration (Traffic): {result['duration_text']}")
        print(f"Duration (Seconds): {result['duration_seconds']}")

if __name__ == "__main__":
    test_traffic()
