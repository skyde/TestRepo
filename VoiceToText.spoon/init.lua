--- === VoiceToText ===
---
--- Record voice and transcribe to text using Google Cloud Speech-to-Text API.
--- Transcribed text is typed at the current cursor position.
---
--- Download: [https://github.com/your-repo/VoiceToText.spoon](https://github.com/your-repo/VoiceToText.spoon)

local obj = {}
obj.__index = obj

-- Metadata
obj.name = "VoiceToText"
obj.version = "1.0"
obj.author = "Voice to Text"
obj.license = "MIT"
obj.homepage = ""

-- Configuration
obj.hotkey = nil
obj.apiKey = nil
obj.recordingPath = "/tmp/voice_recording.wav"
obj.scriptPath = nil
obj.isRecording = false
obj.recordingTask = nil
obj.menubar = nil

--- VoiceToText.logger
--- Variable
--- Logger object used within the Spoon. Can be accessed to set the default log level for the messages coming from the Spoon.
obj.logger = hs.logger.new('VoiceToText')

--- VoiceToText:setApiKey(key)
--- Method
--- Set the Google Cloud API key
---
--- Parameters:
---  * key - Your Google Cloud API key with Speech-to-Text enabled
---
--- Returns:
---  * The VoiceToText object
function obj:setApiKey(key)
    self.apiKey = key
    return self
end

--- VoiceToText:init()
--- Method
--- Initialize the spoon
---
--- Parameters:
---  * None
---
--- Returns:
---  * The VoiceToText object
function obj:init()
    -- Set up the script path relative to the spoon
    self.scriptPath = hs.spoons.scriptPath() .. "voice_to_text.sh"

    -- Create menubar item
    self.menubar = hs.menubar.new()
    if self.menubar then
        self.menubar:setTitle("🎤")
        self.menubar:setTooltip("Voice to Text - Ready")
        self.menubar:setMenu(function()
            return {
                { title = "Start Recording (⌘⇧R)", fn = function() self:toggleRecording() end },
                { title = "-" },
                { title = "Quit", fn = function() self.menubar:delete() end }
            }
        end)
    end

    return self
end

--- VoiceToText:bindHotkeys(mapping)
--- Method
--- Binds hotkeys for VoiceToText
---
--- Parameters:
---  * mapping - A table containing hotkey modifier/key details for:
---    * toggle - Toggle recording on/off (default: Cmd+Shift+R)
---
--- Returns:
---  * The VoiceToText object
function obj:bindHotkeys(mapping)
    local def = {
        toggle = function() self:toggleRecording() end
    }
    hs.spoons.bindHotkeysToSpec(def, mapping)
    return self
end

--- VoiceToText:start()
--- Method
--- Start the VoiceToText spoon with default hotkey (Cmd+Shift+R)
---
--- Parameters:
---  * None
---
--- Returns:
---  * The VoiceToText object
function obj:start()
    self:bindHotkeys({
        toggle = {{"cmd", "shift"}, "r"}
    })
    self.logger.i("VoiceToText started. Press Cmd+Shift+R to record.")
    hs.notify.new({title="VoiceToText", informativeText="Ready! Press ⌘⇧R to record"}):send()
    return self
end

--- VoiceToText:toggleRecording()
--- Method
--- Toggle voice recording on/off
---
--- Parameters:
---  * None
---
--- Returns:
---  * None
function obj:toggleRecording()
    if self.isRecording then
        self:stopRecording()
    else
        self:startRecording()
    end
end

--- VoiceToText:startRecording()
--- Method
--- Start recording audio
---
--- Parameters:
---  * None
---
--- Returns:
---  * None
function obj:startRecording()
    if not self.apiKey then
        hs.notify.new({title="VoiceToText", informativeText="Error: API key not set. Call :setApiKey() first."}):send()
        self.logger.e("API key not set")
        return
    end

    if self.isRecording then
        self.logger.w("Already recording")
        return
    end

    self.isRecording = true
    self.logger.i("Starting recording...")

    -- Update menubar
    if self.menubar then
        self.menubar:setTitle("🔴")
        self.menubar:setTooltip("Voice to Text - Recording...")
    end

    -- Show recording notification
    hs.notify.new({title="VoiceToText", informativeText="Recording... Press ⌘⇧R to stop"}):send()

    -- Start recording using sox/rec
    -- Using rec (part of sox) to record audio
    self.recordingTask = hs.task.new("/usr/bin/env", nil, function(exitCode, stdOut, stdErr)
        -- This callback is called when recording stops
        self.logger.i("Recording process ended")
    end, {"rec", "-r", "16000", "-c", "1", "-b", "16", self.recordingPath})

    self.recordingTask:start()
end

--- VoiceToText:stopRecording()
--- Method
--- Stop recording and transcribe
---
--- Parameters:
---  * None
---
--- Returns:
---  * None
function obj:stopRecording()
    if not self.isRecording then
        self.logger.w("Not currently recording")
        return
    end

    self.isRecording = false
    self.logger.i("Stopping recording...")

    -- Update menubar
    if self.menubar then
        self.menubar:setTitle("⏳")
        self.menubar:setTooltip("Voice to Text - Transcribing...")
    end

    -- Stop the recording task
    if self.recordingTask then
        self.recordingTask:terminate()
        self.recordingTask = nil
    end

    -- Small delay to ensure file is written
    hs.timer.doAfter(0.3, function()
        self:transcribe()
    end)
end

--- VoiceToText:transcribe()
--- Method
--- Transcribe the recorded audio using Google Speech-to-Text API
---
--- Parameters:
---  * None
---
--- Returns:
---  * None
function obj:transcribe()
    hs.notify.new({title="VoiceToText", informativeText="Transcribing..."}):send()

    -- Call the shell script to handle transcription
    local task = hs.task.new(self.scriptPath, function(exitCode, stdOut, stdErr)
        -- Reset menubar
        if self.menubar then
            self.menubar:setTitle("🎤")
            self.menubar:setTooltip("Voice to Text - Ready")
        end

        if exitCode == 0 and stdOut and #stdOut > 0 then
            local text = stdOut:gsub("^%s+", ""):gsub("%s+$", "") -- trim whitespace
            if #text > 0 then
                self.logger.i("Transcription: " .. text)
                self:typeText(text)
                hs.notify.new({title="VoiceToText", informativeText="Typed: " .. text:sub(1, 50) .. (#text > 50 and "..." or "")}):send()
            else
                hs.notify.new({title="VoiceToText", informativeText="No speech detected"}):send()
            end
        else
            self.logger.e("Transcription failed: " .. (stdErr or "unknown error"))
            hs.notify.new({title="VoiceToText", informativeText="Transcription failed: " .. (stdErr or "unknown error"):sub(1, 100)}):send()
        end

        -- Clean up recording file
        os.remove(self.recordingPath)
    end, {self.recordingPath, self.apiKey})

    task:start()
end

--- VoiceToText:typeText(text)
--- Method
--- Type text at the current cursor position
---
--- Parameters:
---  * text - The text to type
---
--- Returns:
---  * None
function obj:typeText(text)
    -- Method 1: Use hs.eventtap.keyStrokes (simple but may have issues with special chars)
    -- hs.eventtap.keyStrokes(text)

    -- Method 2: Use clipboard and paste (more reliable)
    local oldClipboard = hs.pasteboard.getContents()
    hs.pasteboard.setContents(text)
    hs.eventtap.keyStroke({"cmd"}, "v")

    -- Restore old clipboard after a short delay
    hs.timer.doAfter(0.5, function()
        if oldClipboard then
            hs.pasteboard.setContents(oldClipboard)
        end
    end)
end

return obj
