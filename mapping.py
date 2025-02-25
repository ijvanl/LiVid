EVENT_TYPES = [
	"note_on", "note_off", "polytouch", "control_change", "program_change", "aftertouch", "pitchwheel"
]

class Mapping:
	def __init__(self, midi_event, value_mapping):
		self.midi_event = midi_event
		self.value_mapping = value_mapping
	
	@staticmethod
	def default():
		return Mapping(
			MidiEvent("note_on", None, 64, None),
			ValueMapping(None, None)
		)

class MidiEvent:
	def __init__(self, event_type: str, val1: int | None, val2: int | None, val3: int | None):
		self.event_type = event_type
		self.values = [val1, val2, val3]
	
	@staticmethod
	def value_names(name):
		match name:
			case "note_on": return ("channel", "note", "velocity")
			case "note_off": return ("channel", "note", "velocity")
			case "polytouch": return ("channel", "note", "value")
			case "control_change": return ("channel", "control", "value")
			case "program_change": return ("channel", "program", "")
			case "aftertouch": return ("channel", "value", "")
			case "pitchwheel": return ("channel", "pitch", "")
			case _: return ("", "", "")

	def my_value_names(self):
		return self.value_names(self.event_type)
	
	def __eq__(self, value):
		return (
			(self.event_type == value.event_type) and
			((self.values[0] == None) or (value.values[0] == None) or (self.values[0] == value.values[0])) and
			((self.values[1] == None) or (value.values[1] == None) or (self.values[1] == value.values[1])) and
			((self.values[2] == None) or (value.values[2] == None) or (self.values[2] == value.values[2]))
		)

class ValueMapping:
	def __init__(self, lhs_value, rhs_value):
		self.lhs_value = lhs_value
		self.rhs_value = rhs_value