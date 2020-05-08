# name=Akai APC Key 25
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=225886
# Author: Martijn Tromp
# Changelog:
# 23/04/2020 0.01: Implement Play/Pause Button (AKFSM-2)
# 23/04/2020 0.02: Clean up code and handle Note Off
# 23/04/2020 0.03: Add Record and Pattern/Song toggle
# 24/04/2020 0.04: More refactoring, making it easier to map and implement new stuff.
# 02/05/2020 0.05: Implement stuff for calling LEDs on the controller. The played note gets passed to the method.
# 03/05/2020 0.06: Basic fast forward functionality using playback speed. Time in FL studio seems to be mismatched.
#                  Lights work.
#                  Mode switching now using shift modifier.
# 08/05/2020 0.07: fastForward/rewind implemented using transport.fastForward/transport.rewind
#                  kill LEDs when exiting FL Studio


# This import section is loading the back-end code required to execute the script. You may not need all modules that are available for all scripts.

import transport
import mixer
import ui
import midi
import sys
import device

#definition of controller modes
ctrlUser = 0
ctrlTransport = 1
ctrlMixer = 2
ctrlBrowser = 3
ctrlPattern = 4
ctrlPlaylist = 5
controllerMode = 0

# Shift Modifier and Button definition
shiftModifier = 0
shiftButton = 98

#LED colorCodes, for blink add 1 to the value
green = 1
red = 3
yellow = 5

class InitClass():
	def startTheShow(self):
		#set global transport mode
		print ("Welcome Friends!")
		shiftAction = ShiftAction()
		shiftAction.setTransportMode(82) #need to set the note manually, since no note was actually played.
class MidiInHandler():
	# dictionary mapping 
	def noteDict(self, i):
		#dictionary with list of tuples for mapping note to class and method
		dict={
			91:[("GlobalAction", "togglePlay")], # PLAY/PAUSE button on controller
			93:[("GlobalAction", "toggleRecord")], # REC button on controller
			82:[("ShiftAction", "setTransportMode")], #CLIP STOP button on controller
			83:[("ShiftAction", "setMixerMode")], #SOLO button on controller
			84:[("ShiftAction", "setBrowserMode")], 
			85:[("ShiftAction", "setPatternMode")],
			86:[("ShiftAction", "setPlayListMode"), ("TransportAction", "toggleLoopMode")], 
			81:[("ShiftAction", "setUserMode")],
			66:[("TransportAction", "pressRewind"), ("ReleaseAction", "releaseRewind")],
			67:[("TransportAction", "pressFastForward"), ("ReleaseAction", "releaseFastForward")]
		}
		print("Note: " + str(i))
		return dict.get(i,[("notHandled", "")])

	def callAction(self, actionType, action, note):
			callClass = getattr(sys.modules[__name__], actionType)()
			func = getattr(callClass, action) 
			return func(note)

	#Handle the incoming MIDI event
	def OnMidiMsg(self, event):
		global shiftModifier
		print ("controller mode: " + str(controllerMode))
		print("MIDI data: " + str("data1: " + str(event.data1) + " data2: " + str(event.data2) + " midiChan: " +str(event.midiChan) + " midiID: " + str(event.midiId)))
		print("midi property test:" + str(midi.MIDI_NOTEOFF))
		if (event.midiChan == 0 and event.pmeFlags and midi.PME_System != 0): # MidiChan == 0 --> To not interfere with notes played on the keybed
			noteFuncList = self.noteDict(event.data1)
			for noteFunc in noteFuncList:
				actionType = noteFunc[0]
				action = noteFunc[1]
				if (noteFunc[0] == "notHandled" and event.data1 != shiftButton and controllerMode != ctrlUser):
					event.handled = True
				elif (event.midiId == midi.MIDI_NOTEOFF):
					event.handled = True
					if (event.data1 == shiftButton):
						shiftModifier = 0
					elif (actionType == "ReleaseAction" and shiftModifier == 0):
						self.callAction(actionType, action, event.data1)
						event.handled = True
				elif (event.midiId == midi.MIDI_NOTEON):
					event.handled = True
					if (event.data1 == shiftButton):
						shiftModifier = 1
						print ("shiftmodifier on " + str(shiftModifier))
					if (actionType == "ShiftAction" and shiftModifier == 1):
						self.callAction(actionType, action, event.data1)
					elif (actionType == "GlobalAction" and shiftModifier == 0):
						self.callAction(actionType, action, event.data1)
					elif (actionType == "TransportAction" and controllerMode == ctrlTransport and shiftModifier == 0):
						self.callAction(actionType, action, event.data1)
					elif (actionType == "MixerAction" and controllerMode == ctrlMixer and shiftModifier == 0):
						self.callAction(actionType, action, event.data1)
					elif (controllerMode == ctrlUser and event.data1 != shiftButton):
						event.handled = False

#Handle action that use the shift modifier
class ShiftAction():
	def setTransportMode(self, note):
			self.changeMode(ctrlTransport, note)
			print("Transport Mode set")
	def setMixerMode(self, note):
			self.changeMode(ctrlMixer, note)
			print("Mixer Mode set")
	def setBrowserMode(self, note):
			self.changeMode(ctrlBrowser, note)
			print("Browser Mode set")

	def setPatternMode(self, note):
			self.changeMode(ctrlPattern, note)
			print("Pattern Mode set")

	def setPlayListMode(self, note):
			self.changeMode(ctrlPlaylist, note)
			print("PlayList Mode set")

	def setUserMode(self, note):
			self.changeMode(ctrlUser, note)
			print("User Mode set")

	def changeMode(self, ctrlMode, note):
		global controllerMode
		ledCtrl = LedControl()
		ledCtrl.killAllLights()
		controllerMode = ctrlMode
		ledCtrl.setLedMono(note, False)

#Handle actions that trigger on button release
class ReleaseAction():
	def releaseFastForward(self, note):
		if (controllerMode == ctrlTransport):
			transport.fastForward(0)
			ledCtrl = LedControl()
			ledCtrl.setLedOff(note)
			print ("fastForward off")
	def releaseRewind(self, note):
		if (controllerMode == ctrlTransport):
			transport.rewind(0)
			ledCtrl = LedControl()
			ledCtrl.setLedOff(note)
			print ("rewind off")
#Handle actions that will be independent of selected mode.
class GlobalAction():
	def togglePlay(self, note):
		print("isPlaying: " + str(transport.isPlaying()))
		if (transport.isPlaying() == 0):
			transport.start()
			print("Starting Playback")
		elif (transport.isPlaying() == 1):
			transport.stop()
			print("Stopping Playback")
	def toggleRecord(self, note):
		if (transport.isPlaying() == 0): # Only enable recording if not already playing
			transport.record()
			print("Toggle recording")
	


#Handle actions that work in Transport Control ControllerMode
class TransportAction():
	def toggleLoopMode(self, note):
		if (transport.isPlaying() == 0): #Only toggle loop mode if not already playing
			transport.setLoopMode()
			print("Song/Pattern Mode toggled")
	def pressFastForward(self, note):
		transport.fastForward(2)
		ledCtrl = LedControl()
		ledCtrl.setLedMono(note, False)
		print ("fastForward on")
	def pressRewind(self, note):
		transport.rewind(2)
		ledCtrl = LedControl()
		ledCtrl.setLedMono(note, False)
		print ("rewind on")
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
		for i in range(82, 87):
			self.setLedOff(i)
	def killUnderLights(self):
		for i in range(64, 72):
			self.setLedOff(i)
	def killGridLights(self):
		for i in range(40):
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
	
def OnDeInit():
	ledCtrl = LedControl()
	ledCtrl.killAllLights()