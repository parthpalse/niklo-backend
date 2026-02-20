import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.commute_service import CommuteService

def test():
    cs = CommuteService()
    test_cases = ['Ghansoli', 'Churchgate', 'Andheri', 'Panvel', 'Thane', 'Random Address 123']
    for t in test_cases:
        print(f"--- Testing {t} ---")
        try:
            res = cs.calculate_best_route(t, '09:00')
            if 'error' in res:
                print(f"Error: {res['error']}")
            else:
                print(f"Recommendation: {res.get('recommendation')}")
                if res.get('train_route'):
                    print(f"Train Route: {res['train_route']['details']['leg2_train']}")
                else:
                    print("Train Route: None")
        except Exception as e:
            print(f"FATAL Exception: {str(e)}")
            
if __name__ == '__main__':
    test()
