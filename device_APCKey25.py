# name=Akai APC Key 25
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=225886
# Author: Martijn Tromp
# Changelog:
# 23/04/2020 0.01: Implement Play/Pause Button (AKFSM-2)
# 23/04/2020 0.02: Clean up code and handle Note Off
# 23/04/2020 0.03: Add Record and Pattern/Song toggle
# 24/04/2020 0.04: More refactoring, making it easier to map and implement new stuff.
# 02/05/2020 0.05: Implement stuff for calling LEDs on the controller. The played note gets passed to the method.


# This import section is loading the back-end code required to execute the script. You may not need all modules that are available for all scripts.

import transport
import mixer
import ui
import midi
import sys
import device


ctrlUser = 0
ctrlTransport = 1
ctrlMixer = 2
ctrlBrowser = 3
ctrlPattern = 4
ctrlPlaylist = 5
controllerMode = 0

#LED colorCodes, for blink add 1 to the value
green = 1
red = 3
yellow = 5

class InitClass():
	def startTheShow(self):
		#set global transport mode
		print ("Welcome Friends!")
		GlobalAction.setTransportMode(82) #need to set the note manually, since no note was actually played.
class MidiInHandler():
	# dictionary mapping 
	def noteDict(self, i):
		#dictionary with list of tuples for mapping note to class and method
		dict={
			91:[("GlobalAction", "togglePlay")], # PLAY/PAUSE button on controller
			93:[("GlobalAction", "toggleRecord")], # REC button on controller
			98:[("TransportAction", "toggleLoopMode")], # SHIFT button on controller
			82:[("GlobalAction", "setTransportMode")], #CLIP STOP button on controller
			83:[("GlobalAction", "setMixerMode")] #SOLO button on controller
		}
		print("Note: " + str(i))
		return dict.get(i,[("notHandled", "")])

	def callAction(self, actionType, action, note):
			func = getattr(getattr(sys.modules[__name__], actionType), action) 
			return func(note)

	#Handle the incoming MIDI event
	def OnMidiMsg(self, event):
		print ("controller mode: " + str(controllerMode))
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
					actionType = noteFunc[0]
					action = noteFunc[1]
					if (actionType == "GlobalAction"):
						self.callAction(actionType, action, event.data1)
					elif (actionType == "TransportAction" and controllerMode == ctrlTransport):
						self.callAction(actionType, action, event.data1)
					elif (actionType == "MixerAction" and controllerMode == ctrlMixer):
						self.callAction(actionType, action, event.data1)
					else:
						event.handled = False
#Handle actions that will be independent of selected mode.
class GlobalAction():
	def togglePlay(note):
		print("isPlaying: " + str(transport.isPlaying()))
		if (transport.isPlaying() == 0):
			transport.start()
			print("Starting Playback")
		elif (transport.isPlaying() == 1):
			transport.stop()
			print("Stopping Playback")
	def toggleRecord(note):
		if (transport.isPlaying() == 0): # Only enable recording if not already playing
			transport.record()
			print("Toggle recording")
	def setTransportMode(note):
		global controllerMode
		ledCtrl = LedControl()
		ledCtrl.killAllLights()
		controllerMode = ctrlTransport
		ledCtrl.setLedMono(note, False)
		print("Transport Mode set")
	def setMixerMode(note):
		global controllerMode
		ledCtrl = LedControl()
		ledCtrl.killAllLights()
		controllerMode = ctrlMixer
		ledCtrl.setLedMono(note, False)
		print("Mixer Mode set")



#Handle actions that work in Transport Control ControllerMode
class TransportAction():
	def toggleLoopMode(note):
		if (transport.isPlaying() == 0): #Only toggle loop mode if not already playing
			transport.setLoopMode()
			print("Song/Pattern Mode toggled")



#Set them LEDs
class LedControl():
	def __init__(self):
		colorCode = 0

	def setLedMono(self, note, blink):
		if ((64 <= note <= 71) or (82 <= note <= 86)): # 64 to 71: buttons under grid, 82 to 86: buttons to the right of grid.
			if (blink == True):
				colorCode = 2
			else:
				colorCode = 1
			self.sendMidiCommand(note, colorCode)
	def setLedColor(self, note, color, blink):		
		if (note <= 39): #only 8x5 grid is multicolor, which are mapped to midi notes 0 to 39
			if (blink == True):
				colorCode = color + 1
			else:
				colorCode = color
			print ("LED on for note: " + str(note) + " colorCode: " + str(colorCode))
			self.sendMidiCommand(note, colorCode)
	def setLedOff(self, note):
		self.sendMidiCommand(note, 0)
	def killRightSideLights(self):
		for i in range(82, 86):
			self.setLedOff(i)
	def killUnderLights(self):
		for i in range(64, 71):
			self.setLedOff(i)
	def killGridLights(self):
		for i in range(39):
			self.setLedOff(i)
	def killAllLights(self):
		self.killRightSideLights()
		self.killGridLights()
		self.killUnderLights()

	def sendMidiCommand(self, note, colorCode):
		device.midiOutMsg(midi.MIDI_NOTEON + (note << 8) + (colorCode << 16))




MidiIn = MidiInHandler()
start = InitClass()

def OnMidiMsg(event):
	MidiIn.OnMidiMsg(event)

def OnInit():
	start.startTheShow()
	
