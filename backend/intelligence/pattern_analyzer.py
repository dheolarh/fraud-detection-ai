"""
Pattern Analyzer
Analyzes user transaction and login patterns for ML training

Learns:
- Transaction patterns (amounts, categories, times, locations)
- Login patterns (times, devices, locations, frequency)
- Spending behavior (velocity, categories, merchants)
"""

import json
from datetime import datetime
from collections import defaultdict, Counter
import statistics

class PatternAnalyzer:
    """Analyze user patterns from transactions and auth logs"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.patterns = {
            "user_id": user_id,
            "transaction_patterns": {},
            "login_patterns": {},
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def analyze_transactions(self, transactions):
        """Analyze transaction patterns"""
        print(f"Analyzing {len(transactions)} transactions...")
        
        amounts = []
        categories = []
        hours = []
        days_of_week = []
        locations = []
        incoming_amounts = []
        outgoing_amounts = []
        
        for tx in transactions:
            # Parse timestamp
            timestamp = datetime.fromisoformat(tx['timestamp'])
            
            # Collect data
            amounts.append(float(tx['amount']))
            categories.append(tx['category'])
            hours.append(timestamp.hour)
            days_of_week.append(timestamp.weekday())
            locations.append(tx['location'])
            
            if tx['transaction_flow'] == 'incoming':
                incoming_amounts.append(float(tx['amount']))
            else:
                outgoing_amounts.append(float(tx['amount']))
        
        # Calculate statistics
        self.patterns['transaction_patterns'] = {
            # Amount patterns
            'avg_amount': statistics.mean(amounts),
            'median_amount': statistics.median(amounts),
            'min_amount': min(amounts),
            'max_amount': max(amounts),
            'std_amount': statistics.stdev(amounts) if len(amounts) > 1 else 0,
            
            # Flow patterns
            'avg_incoming': statistics.mean(incoming_amounts) if incoming_amounts else 0,
            'avg_outgoing': statistics.mean(outgoing_amounts) if outgoing_amounts else 0,
            'total_incoming': sum(incoming_amounts),
            'total_outgoing': sum(outgoing_amounts),
            
            # Category patterns
            'top_categories': Counter(categories).most_common(10),
            'category_distribution': dict(Counter(categories)),
            
            # Time patterns
            'common_hours': Counter(hours).most_common(5),
            'hour_distribution': dict(Counter(hours)),
            'common_days': Counter(days_of_week).most_common(7),
            
            # Location patterns
            'top_locations': Counter(locations).most_common(10),
            
            # Counts
            'total_transactions': len(transactions),
            'incoming_count': len(incoming_amounts),
            'outgoing_count': len(outgoing_amounts)
        }
        
        print(f"  Avg amount: £{self.patterns['transaction_patterns']['avg_amount']:.2f}")
        print(f"  Top categories: {[cat for cat, _ in self.patterns['transaction_patterns']['top_categories'][:3]]}")
        print(f"  Common hours: {[h for h, _ in self.patterns['transaction_patterns']['common_hours'][:3]]}")
    
    def analyze_logins(self, auth_logs):
        """Analyze login patterns"""
        print(f"\nAnalyzing {len(auth_logs)} auth logs...")
        
        successful_logins = [log for log in auth_logs if log.get('login_success', True)]
        
        devices = []
        hours = []
        days_of_week = []
        locations = []
        login_times = []
        
        for log in successful_logins:
            # Parse timestamp
            timestamp = datetime.fromisoformat(log['timestamp'])
            login_times.append(timestamp)
            
            # Collect data
            devices.append(log['device_type'])
            hours.append(timestamp.hour)
            days_of_week.append(timestamp.weekday())
            locations.append(log['location'])
        
        # Calculate session durations (time between logins)
        login_times.sort()
        session_gaps = []
        for i in range(1, len(login_times)):
            gap = (login_times[i] - login_times[i-1]).total_seconds() / 3600  # hours
            if gap < 168:  # Less than a week
                session_gaps.append(gap)
        
        self.patterns['login_patterns'] = {
            # Device patterns
            'device_distribution': dict(Counter(devices)),
            'primary_device': Counter(devices).most_common(1)[0][0] if devices else None,
            
            # Time patterns
            'common_login_hours': Counter(hours).most_common(10),
            'hour_distribution': dict(Counter(hours)),
            'common_login_days': Counter(days_of_week).most_common(7),
            
            # Location patterns
            'top_login_locations': Counter(locations).most_common(5),
            'location_distribution': dict(Counter(locations)),
            
            # Frequency patterns
            'avg_session_gap_hours': statistics.mean(session_gaps) if session_gaps else 0,
            'median_session_gap_hours': statistics.median(session_gaps) if session_gaps else 0,
            
            # Counts
            'total_logins': len(successful_logins),
            'failed_logins': len(auth_logs) - len(successful_logins)
        }
        
        print(f"  Primary device: {self.patterns['login_patterns']['primary_device']}")
        print(f"  Common hours: {[h for h, _ in self.patterns['login_patterns']['common_login_hours'][:3]]}")
        print(f"  Avg session gap: {self.patterns['login_patterns']['avg_session_gap_hours']:.1f} hours")
    
    def save_patterns(self, filename):
        """Save patterns to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.patterns, f, indent=2)
        print(f"\n✅ Saved patterns to {filename}")
    
    def get_patterns(self):
        """Return patterns dictionary"""
        return self.patterns


if __name__ == "__main__":
    # Test with sample data
    print("Pattern Analyzer - Test Mode")
    print("="*70)
    
    # This would normally load from database
    # For now, just demonstrate the structure
    analyzer = PatternAnalyzer("HOV-2426-1226")
    print("\n✅ Pattern analyzer ready")
    print("Use this to analyze transactions and auth logs from the database")
