# name=Akai APC Key 25
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=225886
# Author: Martijn Tromp
# Changelog:
# 23/04/2020 0.01: Implement Play/Pause Button (AKFSM-2)
# 23/04/2020 0.02: Clean up code and handle Note Off
# 23/04/2020 0.03: Add Record and Pattern/Song toggle
# 24/04/2020 0.04: More refactoring, making it easier to map and implement new stuff.


# This import section is loading the back-end code required to execute the script. You may not need all modules that are available for all scripts.

import transport
import mixer
import ui
import midi
import sys

class MidiInHandler():
	# dictionary mapping 
	def noteDict(self, i):
		#dictionary with list of tuples for mapping note to class and method
		dict={
			91:[("GlobalAction", "togglePlay")], # PLAY/PAUSE button on controller
			93:[("GlobalAction", "toggleRecord")], # REC button on controller
			98:[("GlobalAction", "toggleLoopMode")] # SHIFT button on controller
		}
		print("Note: " + str(i))
		return dict.get(i,[("notHandled", "")])

	#Handle the incoming MIDI event
	def OnMidiMsg(self, event):
		print("MIDI data: " + str("data1: " + str(event.data1) + " data2: " + str(event.data2) + " midiChan: " +str(event.midiChan) + " midiID: " + str(event.midiId)))
		if (event.midiChan == 0 and event.pmeFlags and midi.PME_System != 0): # MidiChan == 0 --> To not interfere with notes played on the keybed
			noteFuncList = self.noteDict(event.data1)
			# I want to be able to have a single note perform multiple actions in the future, as well as selecting different modes on the controller.
			for noteFunc in noteFuncList:
				if (noteFunc[0] == "notHandled"):
					event.handled = False
				elif (event.midiId == midi.MIDI_NOTEOFF):
					event.handled = True
				elif (event.midiId == midi.MIDI_NOTEON):
					event.handled = True
					func = getattr(getattr(sys.modules[__name__], noteFunc[0]), noteFunc[1]) 
					func()

#Handle actions that will be independent of selected mode.
class GlobalAction():

	def togglePlay():
		print("isPlaying: " + str(transport.isPlaying()))
		if (transport.isPlaying() == 0):
			transport.start()
			print("Starting Playback")
		elif (transport.isPlaying() == 1):
			transport.stop()
			print("Stopping Playback")
	def toggleRecord():
		if (transport.isPlaying() == 0): # Only enable recording if not already playing
			transport.record()
			print("Toggle recording")
	def toggleLoopMode():
		if (transport.isPlaying() == 0): #Only toggle loop mode if not already playing
			transport.setLoopMode()
			print("Song/Pattern Mode toggled")

MidiIn = MidiInHandler()

def OnMidiMsg(event):
	MidiIn.OnMidiMsg(event)
