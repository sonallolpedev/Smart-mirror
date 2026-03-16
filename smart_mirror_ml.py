"""
Smart Mirror Advanced AI/ML Module
Provides advanced features like sentiment analysis, schedule optimization, and predictive reflections
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from typing import List, Dict, Tuple
import anthropic

class SmartMirrorML:
    """Machine Learning enhancements for Smart Mirror"""
    
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.schedule_history = []
        self.mood_history = []
        self.reflection_history = []
        
    def analyze_schedule_patterns(self, events: List[Dict]) -> Dict:
        """
        Analyze schedule patterns to optimize daily routine
        
        Args:
            events: List of calendar events
            
        Returns:
            Dictionary with schedule insights
        """
        if not events:
            return {'insights': 'No events to analyze'}
        
        # Extract time patterns
        event_times = [self._time_to_minutes(event['time']) for event in events]
        event_durations = [event.get('duration', 30) for event in events]
        
        # Calculate statistics
        avg_time_between = self._calculate_gaps(event_times, event_durations)
        total_scheduled = sum(event_durations)
        
        insights = {
            'total_scheduled_minutes': total_scheduled,
            'total_scheduled_hours': round(total_scheduled / 60, 1),
            'average_gap_between_events': round(avg_time_between, 1),
            'busiest_hours': self._find_busiest_hours(event_times),
            'free_time_blocks': self._find_free_blocks(event_times, event_durations),
            'event_count': len(events),
            'recommendation': self._generate_schedule_recommendation(events, total_scheduled)
        }
        
        return insights
    
    def predict_optimal_break_time(self, events: List[Dict]) -> Dict:
        """
        Predict the best time for breaks based on schedule
        
        Args:
            events: List of calendar events
            
        Returns:
            Dictionary with break time recommendations
        """
        if not events:
            return {'recommended_break': 'Take breaks between tasks'}
        
        event_times = [self._time_to_minutes(event['time']) for event in events]
        event_durations = [event.get('duration', 30) for event in events]
        
        # Find gaps longer than 15 minutes
        gaps = []
        for i in range(len(event_times) - 1):
            gap_start = event_times[i] + event_durations[i]
            gap_end = event_times[i + 1]
            gap_duration = gap_end - gap_start
            
            if gap_duration > 15:
                gaps.append({
                    'start_time': self._minutes_to_time(gap_start),
                    'end_time': self._minutes_to_time(gap_end),
                    'duration_minutes': gap_duration,
                    'suitability_score': self._score_break_quality(gap_start, gap_duration)
                })
        
        if gaps:
            best_break = max(gaps, key=lambda x: x['suitability_score'])
            return {
                'recommended_break_time': best_break['start_time'],
                'duration_minutes': best_break['duration_minutes'],
                'break_type': self._suggest_break_type(best_break['duration_minutes']),
                'all_available_breaks': gaps[:3]
            }
        else:
            return {'recommended_break': 'No suitable break time found. Consider reducing workload.'}
    
    def generate_contextual_reflection(self, 
                                      current_time: str,
                                      mood: str = 'neutral',
                                      schedule_pressure: str = 'medium') -> str:
        """
        Generate reflection based on time of day and current context
        
        Args:
            current_time: Current time in HH:MM format
            mood: Current mood (positive, neutral, stressed)
            schedule_pressure: Schedule pressure level (low, medium, high)
            
        Returns:
            AI-generated reflection
        """
        hour = int(current_time.split(':')[0])
        
        # Determine time of day
        if 5 <= hour < 12:
            time_period = 'morning'
            theme = 'motivation and readiness'
        elif 12 <= hour < 17:
            time_period = 'afternoon'
            theme = 'focus and productivity'
        elif 17 <= hour < 21:
            time_period = 'evening'
            theme = 'reflection and gratitude'
        else:
            time_period = 'night'
            theme = 'rest and recovery'
        
        prompt = f"""Generate a short, personalized daily reflection for {time_period} ({current_time}).
        
Context:
- Current mood: {mood}
- Schedule pressure: {schedule_pressure}
- Theme: {theme}

Requirements:
- Keep it under 15 words
- Make it relevant to the time of day
- Address the current mood and schedule
- Be inspirational but realistic
- Return ONLY the reflection text, nothing else"""
        
        try:
            message = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Error generating reflection: {e}")
            return self._get_default_reflection(time_period)
    
    def analyze_mood_trends(self, mood_entries: List[Dict]) -> Dict:
        """
        Analyze mood trends over time
        
        Args:
            mood_entries: List of mood entries with timestamps and mood values
            
        Returns:
            Dictionary with mood analysis
        """
        if not mood_entries:
            return {'status': 'No mood data available'}
        
        moods = [entry['mood'] for entry in mood_entries]
        mood_values = {'positive': 1, 'neutral': 0, 'stressed': -1, 'negative': -2}
        numeric_moods = [mood_values.get(m, 0) for m in moods]
        
        analysis = {
            'average_mood': round(np.mean(numeric_moods), 2),
            'mood_variance': round(np.var(numeric_moods), 2),
            'trend': self._determine_trend(numeric_moods),
            'most_common_mood': max(set(moods), key=moods.count),
            'mood_distribution': {
                'positive': moods.count('positive') / len(moods) * 100,
                'neutral': moods.count('neutral') / len(moods) * 100,
                'stressed': moods.count('stressed') / len(moods) * 100,
                'negative': moods.count('negative') / len(moods) * 100
            }
        }
        
        return analysis
    
    def detect_overwork_patterns(self, events: List[Dict]) -> Dict:
        """
        Detect and alert about overwork patterns
        
        Args:
            events: List of calendar events
            
        Returns:
            Dictionary with overwork analysis
        """
        if not events:
            return {'status': 'insufficient_data'}
        
        event_durations = [event.get('duration', 30) for event in events]
        total_minutes = sum(event_durations)
        total_hours = total_minutes / 60
        
        # Work events analysis
        work_events = [e for e in events if e.get('type') == 'work']
        work_minutes = sum([e.get('duration', 30) for e in work_events])
        work_hours = work_minutes / 60
        
        # Personal events analysis
        personal_events = [e for e in events if e.get('type') == 'personal']
        personal_minutes = sum([e.get('duration', 30) for e in personal_events])
        personal_hours = personal_minutes / 60
        
        # Calculate work-life balance
        work_life_ratio = work_hours / personal_hours if personal_hours > 0 else work_hours
        
        alerts = []
        if work_hours > 8:
            alerts.append('⚠️ Over 8 hours of work scheduled')
        if total_hours > 10:
            alerts.append('⚠️ Over 10 hours of total activities')
        if work_life_ratio > 3:
            alerts.append('⚠️ Work significantly exceeds personal time')
        if len([e for e in events if e.get('duration', 30) >= 120]) > 2:
            alerts.append('⚠️ Multiple long sessions (2+ hours) scheduled')
        
        analysis = {
            'total_scheduled_hours': round(total_hours, 1),
            'work_hours': round(work_hours, 1),
            'personal_hours': round(personal_hours, 1),
            'work_life_ratio': round(work_life_ratio, 2),
            'alerts': alerts if alerts else ['✅ Schedule looks balanced'],
            'recommendation': self._generate_workload_recommendation(work_hours, personal_hours, alerts)
        }
        
        return analysis
    
    def optimize_daily_routine(self, events: List[Dict], preferences: Dict = None) -> List[Dict]:
        """
        Suggest optimizations to daily routine
        
        Args:
            events: List of calendar events
            preferences: User preferences for schedule optimization
            
        Returns:
            Optimized event list with suggestions
        """
        if not events:
            return []
        
        optimized = []
        
        # Group events by type
        work_events = [e for e in events if e.get('type') == 'work']
        personal_events = [e for e in events if e.get('type') == 'personal']
        
        # Suggested optimizations
        suggestions = []
        
        # Check for long sessions without breaks
        for event in work_events:
            if event.get('duration', 30) > 120:
                suggestions.append({
                    'event': event['title'],
                    'suggestion': 'Break into smaller sessions with 10-minute breaks',
                    'reasoning': 'Long sessions reduce productivity'
                })
        
        # Check for back-to-back meetings
        sorted_events = sorted(events, key=lambda e: e['time'])
        for i in range(len(sorted_events) - 1):
            current_end = (self._time_to_minutes(sorted_events[i]['time']) + 
                          sorted_events[i].get('duration', 30))
            next_start = self._time_to_minutes(sorted_events[i + 1]['time'])
            
            if next_start - current_end < 5:
                suggestions.append({
                    'event': sorted_events[i]['title'],
                    'suggestion': f"Buffer time before '{sorted_events[i + 1]['title']}'",
                    'reasoning': 'Context switching requires mental break'
                })
        
        # Check for early morning overload
        morning_events = [e for e in events if self._time_to_minutes(e['time']) < 600]
        if len(morning_events) > 3:
            suggestions.append({
                'event': 'Morning',
                'suggestion': 'Move non-urgent tasks to afternoon',
                'reasoning': 'Mental energy peaks later in morning'
            })
        
        return {
            'optimized_schedule': sorted_events,
            'suggestions': suggestions,
            'optimization_score': round(100 - len(suggestions) * 5, 1)
        }
    
    # Helper methods
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _calculate_gaps(self, times: List[int], durations: List[int]) -> float:
        """Calculate average gap between events"""
        if len(times) < 2:
            return 0
        
        gaps = []
        for i in range(len(times) - 1):
            gap = times[i + 1] - (times[i] + durations[i])
            if gap > 0:
                gaps.append(gap)
        
        return np.mean(gaps) if gaps else 0
    
    def _find_busiest_hours(self, times: List[int]) -> List[str]:
        """Find the busiest hours of the day"""
        hour_counts = defaultdict(int)
        for t in times:
            hour = t // 60
            hour_counts[hour] += 1
        
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{h:02d}:00" for h, _ in sorted_hours[:3]]
    
    def _find_free_blocks(self, times: List[int], durations: List[int]) -> List[Dict]:
        """Find free time blocks"""
        if not times:
            return []
        
        free_blocks = []
        last_end = 0
        
        for i, start in enumerate(sorted(times)):
            if start > last_end:
                free_blocks.append({
                    'start': self._minutes_to_time(last_end),
                    'end': self._minutes_to_time(start),
                    'duration': start - last_end
                })
            last_end = start + durations[i]
        
        # Add time after last event until midnight
        if last_end < 1440:
            free_blocks.append({
                'start': self._minutes_to_time(last_end),
                'end': '23:59',
                'duration': 1440 - last_end
            })
        
        return [b for b in free_blocks if b['duration'] > 30][:3]
    
    def _score_break_quality(self, time_minutes: int, duration: int) -> float:
        """Score how suitable a time block is for a break"""
        hour = time_minutes // 60
        
        # Prefer late morning or early afternoon for breaks
        quality = 0
        if 10 <= hour <= 11:
            quality += 10  # Morning energy dip
        elif 14 <= hour <= 15:
            quality += 8   # Post-lunch slump
        elif 16 <= hour <= 17:
            quality += 6   # Afternoon energy dip
        
        # Longer breaks score higher
        if duration >= 30:
            quality += 5
        
        return quality
    
    def _suggest_break_type(self, duration: int) -> str:
        """Suggest type of break based on duration"""
        if duration < 15:
            return 'Quick stretch (5 min)'
        elif duration < 30:
            return 'Walk break (10-15 min)'
        elif duration < 60:
            return 'Lunch/meal break'
        else:
            return 'Extended break - consider personal activity'
    
    def _determine_trend(self, values: List[float]) -> str:
        """Determine trend from values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Calculate moving average
        recent = np.mean(values[-3:]) if len(values) >= 3 else np.mean(values)
        previous = np.mean(values[:-3]) if len(values) >= 3 else values[0]
        
        if recent > previous + 0.2:
            return 'improving'
        elif recent < previous - 0.2:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_schedule_recommendation(self, events: List[Dict], total_minutes: int) -> str:
        """Generate schedule recommendation"""
        hours = total_minutes / 60
        
        if hours < 4:
            return 'Light schedule - good opportunity for deep work or self-care'
        elif hours < 8:
            return 'Balanced schedule - manageable workload'
        elif hours < 10:
            return 'Busy schedule - ensure adequate breaks'
        else:
            return 'Very busy schedule - consider rescheduling some tasks'
    
    def _generate_workload_recommendation(self, work_h: float, personal_h: float, alerts: List) -> str:
        """Generate workload recommendation"""
        if not alerts or alerts[0].startswith('✅'):
            return 'Great work-life balance! Maintain this schedule.'
        elif work_h > 8 and personal_h < 2:
            return 'Consider adding personal time - productivity decreases with overwork'
        else:
            return 'Review and redistribute workload to ensure sustainability'
    
    def _get_default_reflection(self, time_period: str) -> str:
        """Get default reflection for time period"""
        reflections = {
            'morning': 'Start your day with intention and purpose.',
            'afternoon': 'Stay focused and break tasks into smaller steps.',
            'evening': 'Reflect on today\'s accomplishments with gratitude.',
            'night': 'Rest well - tomorrow brings new opportunities.'
        }
        return reflections.get(time_period, 'You\'ve got this!')


# Example usage
if __name__ == '__main__':
    ml = SmartMirrorML()
    
    # Sample events
    sample_events = [
        {'title': 'Morning Routine', 'time': '08:00', 'duration': 30, 'type': 'personal'},
        {'title': 'Team Standup', 'time': '10:30', 'duration': 15, 'type': 'work'},
        {'title': 'Deep Work', 'time': '11:00', 'duration': 120, 'type': 'work'},
        {'title': 'Lunch Break', 'time': '13:00', 'duration': 60, 'type': 'personal'},
        {'title': 'Meetings', 'time': '14:15', 'duration': 90, 'type': 'work'},
        {'title': 'Evening Walk', 'time': '18:30', 'duration': 30, 'type': 'personal'},
    ]
    
    # Test functions
    print("Schedule Analysis:")
    print(json.dumps(ml.analyze_schedule_patterns(sample_events), indent=2))
    print("\nOptimal Break Time:")
    print(json.dumps(ml.predict_optimal_break_time(sample_events), indent=2))
    print("\nOverwork Detection:")
    print(json.dumps(ml.detect_overwork_patterns(sample_events), indent=2))
    print("\nRoutine Optimization:")
    print(json.dumps(ml.optimize_daily_routine(sample_events), indent=2))
    print("\nContextual Reflection:")
    print(ml.generate_contextual_reflection('14:30', mood='neutral', schedule_pressure='medium'))
