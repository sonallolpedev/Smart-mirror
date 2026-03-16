from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class WidgetSystem:
    def __init__(self):
        self.widgets = {
            'clock': {'x': 0, 'y': 0, 'width': 2, 'height': 1},
            'weather': {'x': 2, 'y': 0, 'width': 2, 'height': 1},
            'calendar': {'x': 0, 'y': 1, 'width': 4, 'height': 2},
            'reflection': {'x': 0, 'y': 3, 'width': 4, 'height': 1}
        }
    
    def save_layout(self, widget_id, position):
        """Save custom widget positions"""
        self.widgets[widget_id] = position
        # Save to database
        return True
    
    def get_layout(self):
        """Get saved layout"""
        return self.widgets