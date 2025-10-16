<!-- 8d27c69a-51be-428a-bbe9-f067c375dca5 1951f66a-aab1-4190-87f6-fe347fad9033 -->
# Unified Button State Management - Official Dash Approach

## Architecture Overview

**Core Principle**: Use Dash Clientside Callbacks (official recommended way) + dcc.Store for centralized state management. Only use `dash_clientside.set_props` for external events (WebSocket, custom event listeners).

**State Flow**:

```
User Action → Update dcc.Store → Clientside Callback → Update Button UI
                     ↑
              External Events (WebSocket, etc.) use set_props
```

## Key Technical Decisions

1. **Icon Strategy**: Keep icons fixed in Python (DashIconify/AntdIcon), only update `style` (colors) and state properties (`loading`, `disabled`) via clientside callbacks
2. **Avoid Duplicates**: Use single dcc.Store as state source, multiple clientside callbacks read from it (no duplicate outputs)
3. **TTS Config**: Check `AUTO_PLAY_DEFAULT` only in Scenario 1 (text chat), always play in Scenario 2 (voice recording)
4. **Hybrid Integration**: Server callbacks for business logic, clientside callbacks for UI updates

## Files to Modify

### Create New

- `assets/css/unified_buttons.css` - Unified button styles
- `assets/js/unified_button_state_manager.js` - State manager class (refactored for Store-based approach)

### Modify Existing

- `components/chat_input_area.py` - Update button styles to be consistent (40px × 40px, borderRadius 8px)
- `app.py` - Register clientside callbacks
- `callbacks/core_pages_c/chat_input_area_c.py` - Keep server-side business logic
- `assets/js/voice_recorder_enhanced.js` - Trigger state updates via Store
- `assets/js/voice_player_enhanced.js` - Trigger state updates via Store
- `assets/js/voice_websocket_manager.js` - Use set_props for WebSocket events

## Implementation Plan

### Phase 1: Unified Button Styles (2 hours)

#### 1.1 Create CSS file

Create `assets/css/unified_buttons.css`:

```css
/* Unified button base styles */
.unified-button {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

/* State colors */
.btn-available { background-color: #1890ff !important; }
.btn-processing { background-color: #faad14 !important; }
.btn-active { background-color: #ff4d4f !important; }
.btn-playing { background-color: #52c41a !important; }
.btn-disabled { background-color: #d9d9d9 !important; }
```

#### 1.2 Update button components

Modify `components/chat_input_area.py` (lines 154-216):

**Text Button** (keep AntdIcon, update style):

```python
fac.AntdButton(
    icon=fac.AntdIcon(icon="antd-arrow-up"),
    id="ai-chat-x-send-btn",
    type="primary",
    shape="circle",
    loading=False,
    disabled=False,
    style={
        "padding": "0",
        "width": "40px",
        "height": "40px",
        "borderRadius": "8px",
        "backgroundColor": "#1890ff",
        "borderColor": "#1890ff"
    }
)
```

**Recording Button** (keep DashIconify, update style):

```python
fac.AntdButton(
    id="voice-record-button",
    icon=DashIconify(icon="proicons:microphone", width=20, height=20),
    type="primary",
    size="large",
    title="开始录音",
    style={
        "padding": "8px",
        "width": "40px",
        "height": "40px",
        "borderRadius": "8px",
        "backgroundColor": "#1890ff",
        "borderColor": "#1890ff",
        "boxShadow": "0 2px 4px rgba(24, 144, 255, 0.2)"
    }
)
```

**Call Button** (keep DashIconify, update style):

```python
fac.AntdButton(
    id="voice-call-btn",
    icon=DashIconify(icon="bi:telephone", width=20, height=20),
    type="primary",
    size="large",
    title="实时语音通话",
    style={
        "padding": "8px",
        "width": "40px",
        "height": "40px",
        "borderRadius": "8px",
        "backgroundColor": "#52c41a",
        "borderColor": "#52c41a",
        "boxShadow": "0 2px 4px rgba(82, 196, 26, 0.2)"
    }
)
```

### Phase 2: Central State Store Setup (1 hour)

#### 2.1 Add state Store to layout

In `views/core_pages/chat.py` or appropriate layout file, add:

```python
dcc.Store(id='unified-button-state', data={'state': 'idle', 'timestamp': 0}),
dcc.Store(id='button-event-trigger', data=None)  # For external events
```

#### 2.2 Define state schema

State structure:

```javascript
{
    state: 'idle' | 'text_processing' | 'recording' | 'voice_processing' | 
           'preparing_tts' | 'playing_tts' | 'calling',
    timestamp: <unix_timestamp>,
    metadata: {
        from_scenario: 'text' | 'voice' | 'call',
        auto_play: true | false  // TTS config
    }
}
```

### Phase 3: Refactor State Manager (3 hours)

#### 3.1 Refactor unified_button_state_manager.js

Rewrite to support Store-based approach:

```javascript
class UnifiedButtonStateManager {
    constructor() {
        this.GLOBAL_STATES = {
            IDLE: 'idle',
            TEXT_PROCESSING: 'text_processing',
            RECORDING: 'recording',
            VOICE_PROCESSING: 'voice_processing',
            PREPARING_TTS: 'preparing_tts',
            PLAYING_TTS: 'playing_tts',
            CALLING: 'calling'
        };
        
        this.currentState = this.GLOBAL_STATES.IDLE;
        console.log('UnifiedButtonStateManager initialized (Store-based)');
    }
    
    // Get button styles for each state (used by clientside callbacks)
    getButtonStyles(state) {
        const styles = this.getStateStyles(state);
        return [
            styles.textButton,      // Text button style
            styles.textLoading,     // Text button loading
            styles.textDisabled,    // Text button disabled
            styles.recordButton,    // Record button style
            styles.recordDisabled,  // Record button disabled
            styles.callButton,      // Call button style
            styles.callDisabled     // Call button disabled
        ];
    }
    
    getStateStyles(state) {
        const states = {
            [this.GLOBAL_STATES.IDLE]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: false,
                textDisabled: false,
                recordButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                recordDisabled: false,
                callButton: { backgroundColor: '#52c41a', borderColor: '#52c41a' },
                callDisabled: false
            },
            [this.GLOBAL_STATES.TEXT_PROCESSING]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                recordDisabled: true,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            [this.GLOBAL_STATES.RECORDING]: {
                textButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                textLoading: false,
                textDisabled: true,
                recordButton: { backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' },
                recordDisabled: false,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            [this.GLOBAL_STATES.VOICE_PROCESSING]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#faad14', borderColor: '#faad14' },
                recordDisabled: true,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            [this.GLOBAL_STATES.PREPARING_TTS]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#faad14', borderColor: '#faad14' },
                recordDisabled: true,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            [this.GLOBAL_STATES.PLAYING_TTS]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#52c41a', borderColor: '#52c41a' },
                recordDisabled: false,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            [this.GLOBAL_STATES.CALLING]: {
                textButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                textLoading: false,
                textDisabled: true,
                recordButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                recordDisabled: true,
                callButton: { backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' },
                callDisabled: false
            }
        };
        
        return states[state] || states[this.GLOBAL_STATES.IDLE];
    }
    
    // Helper methods for state determination (used by callbacks)
    determineNewState(currentState, eventType, metadata) {
        // State transition logic based on events
        // Returns new state object for Store
    }
    
    // Input validation
    checkInputContent() {
        const input = document.getElementById('ai-chat-x-input');
        if (!input) return false;
        const value = input.value || '';
        return value.trim().length > 0;
    }
    
    // Get TTS auto-play setting
    getAutoPlaySetting() {
        if (window.voiceConfig && typeof window.voiceConfig.AUTO_PLAY_DEFAULT !== 'undefined') {
            return window.voiceConfig.AUTO_PLAY_DEFAULT;
        }
        if (window.voiceConfig && typeof window.voiceConfig.autoPlay !== 'undefined') {
            return window.voiceConfig.autoPlay;
        }
        return true; // Default to enabled
    }
}

// Initialize global instance
window.unifiedButtonStateManager = new UnifiedButtonStateManager();
```

### Phase 4: Register Clientside Callbacks (4 hours)

#### 4.1 State update callback

In `app.py`, add callback to update central state:

```python
app.clientside_callback(
    """
    function(text_clicks, input_value, sse_event, recording_event, current_state) {
        // Determine which event triggered
        const ctx = dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }
        
        const triggered = ctx.triggered[0];
        const triggeredId = triggered.prop_id.split('.')[0];
        
        // Get state manager
        const manager = window.unifiedButtonStateManager;
        if (!manager) return window.dash_clientside.no_update;
        
        let newState = current_state || {state: 'idle', timestamp: 0};
        const now = Date.now();
        
        // Handle text button click
        if (triggeredId === 'ai-chat-x-send-btn') {
            if (!manager.checkInputContent()) {
                // Show warning (handled separately)
                return window.dash_clientside.no_update;
            }
            newState = {
                state: 'text_processing',
                timestamp: now,
                metadata: {from_scenario: 'text', auto_play: manager.getAutoPlaySetting()}
            };
        }
        
        // Handle SSE completion
        else if (triggeredId === 'ai-chat-x-sse-completed-receiver') {
            const metadata = current_state.metadata || {};
            const autoPlay = metadata.auto_play !== false;
            
            // Check scenario: only check auto_play for text scenario
            if (metadata.from_scenario === 'text' && !autoPlay) {
                newState = {state: 'idle', timestamp: now, metadata: {}};
            } else {
                newState = {
                    state: 'preparing_tts',
                    timestamp: now,
                    metadata: metadata
                };
            }
        }
        
        // Handle external events (from button-event-trigger Store)
        else if (triggeredId === 'button-event-trigger') {
            if (!recording_event) return window.dash_clientside.no_update;
            
            const eventType = recording_event.type;
            if (eventType === 'recording_start') {
                newState = {
                    state: 'recording',
                    timestamp: now,
                    metadata: {from_scenario: 'voice'}
                };
            }
            else if (eventType === 'recording_stop') {
                newState = {
                    state: 'voice_processing',
                    timestamp: now,
                    metadata: {from_scenario: 'voice'}
                };
            }
            else if (eventType === 'stt_complete') {
                newState = {
                    state: 'text_processing',
                    timestamp: now,
                    metadata: {from_scenario: 'voice', auto_play: true}
                };
            }
            else if (eventType === 'tts_start') {
                newState = {
                    state: 'playing_tts',
                    timestamp: now,
                    metadata: current_state.metadata || {}
                };
            }
            else if (eventType === 'tts_complete' || eventType === 'tts_stop') {
                newState = {state: 'idle', timestamp: now, metadata: {}};
            }
        }
        
        return newState;
    }
    """,
    Output('unified-button-state', 'data'),
    [
        Input('ai-chat-x-send-btn', 'n_clicks'),
        Input('ai-chat-x-sse-completed-receiver', 'data-completion-event'),
        Input('button-event-trigger', 'data')
    ],
    [
        State('ai-chat-x-input', 'value'),
        State('unified-button-state', 'data')
    ],
    prevent_initial_call=True
)
```

#### 4.2 UI update callback

Add callback to update button UI based on state:

```python
app.clientside_callback(
    """
    function(state_data) {
        if (!state_data || !window.unifiedButtonStateManager) {
            return [
                window.dash_clientside.no_update,
                window.dash_clientside.no_update,
                window.dash_clientside.no_update,
                window.dash_clientside.no_update,
                window.dash_clientside.no_update,
                window.dash_clientside.no_update,
                window.dash_clientside.no_update
            ];
        }
        
        const state = state_data.state || 'idle';
        const styles = window.unifiedButtonStateManager.getButtonStyles(state);
        
        return styles;  // Returns [textStyle, textLoading, textDisabled, recordStyle, recordDisabled, callStyle, callDisabled]
    }
    """,
    [
        Output('ai-chat-x-send-btn', 'style'),
        Output('ai-chat-x-send-btn', 'loading'),
        Output('ai-chat-x-send-btn', 'disabled'),
        Output('voice-record-button', 'style'),
        Output('voice-record-button', 'disabled'),
        Output('voice-call-btn', 'style'),
        Output('voice-call-btn', 'disabled')
    ],
    Input('unified-button-state', 'data'),
    prevent_initial_call=True
)
```

#### 4.3 Input validation callback

Add callback for empty input warning:

```python
app.clientside_callback(
    """
    function(n_clicks, input_value) {
        if (!n_clicks) return window.dash_clientside.no_update;
        
        const manager = window.unifiedButtonStateManager;
        if (!manager) return window.dash_clientside.no_update;
        
        if (!manager.checkInputContent()) {
            return {
                'content': '请输入消息内容',
                'type': 'warning',
                'duration': 2
            };
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('global-message', 'children'),
    Input('ai-chat-x-send-btn', 'n_clicks'),
    State('ai-chat-x-input', 'value'),
    prevent_initial_call=True
)
```

### Phase 5: Integrate with Voice Components (3 hours)

#### 5.1 Update voice_recorder_enhanced.js

Modify recording methods to trigger Store updates:

```javascript
async startRecording() {
    try {
        // ... existing recording logic ...
        
        // Trigger state update via Store (use set_props for external event)
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props('button-event-trigger', {
                data: {type: 'recording_start', timestamp: Date.now()}
            });
        }
    } catch (error) {
        console.error('Recording error:', error);
    }
}

async stopRecording() {
    try {
        // ... existing stop logic ...
        
        // Trigger state update
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props('button-event-trigger', {
                data: {type: 'recording_stop', timestamp: Date.now()}
            });
        }
    } catch (error) {
        console.error('Stop recording error:', error);
    }
}

onSTTComplete(result) {
    // ... existing STT handling ...
    
    // Trigger state update
    if (window.dash_clientside && window.dash_clientside.set_props) {
        window.dash_clientside.set_props('button-event-trigger', {
            data: {type: 'stt_complete', timestamp: Date.now()}
        });
    }
}
```

#### 5.2 Update voice_player_enhanced.js

Modify playback methods:

```javascript
async play(audioData) {
    try {
        // ... existing play logic ...
        
        // Trigger state update
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props('button-event-trigger', {
                data: {type: 'tts_start', timestamp: Date.now()}
            });
        }
    } catch (error) {
        console.error('Play error:', error);
        this.onPlaybackError(error);
    }
}

onPlaybackComplete() {
    // ... existing completion logic ...
    
    // Trigger state update
    if (window.dash_clientside && window.dash_clientside.set_props) {
        window.dash_clientside.set_props('button-event-trigger', {
            data: {type: 'tts_complete', timestamp: Date.now()}
        });
    }
}

stop() {
    // ... existing stop logic ...
    
    // Trigger state update
    if (window.dash_clientside && window.dash_clientside.set_props) {
        window.dash_clientside.set_props('button-event-trigger', {
            data: {type: 'tts_stop', timestamp: Date.now()}
        });
    }
}
```

#### 5.3 Update voice_websocket_manager.js

Add Store triggers for WebSocket events:

```javascript
handleMessage(event) {
    const data = JSON.parse(event.data);
    
    // ... existing message handling ...
    
    // For events that need button state updates, trigger via Store
    if (data.type === 'connection_established') {
        // This is an external event, use set_props
        if (window.dash_clientside && window.dash_clientside.set_props) {
            // Update connection status stores as before
            // State manager will handle button states based on callbacks
        }
    }
}
```

### Phase 6: Server-Side Integration (2 hours)

#### 6.1 Keep server-side business logic

In `callbacks/core_pages_c/chat_input_area_c.py`, maintain existing callback but add validation:

```python
@app.callback(
    [
        Output('ai-chat-x-messages-store', 'data'),
        Output('ai-chat-x-input', 'value'),
        Output('ai-chat-x-send-btn', 'loading', allow_duplicate=True),
        Output('ai-chat-x-send-btn', 'disabled', allow_duplicate=True),
        Output('voice-enable-voice', 'data')
    ],
    [
        Input({'type': 'chat-topic', 'index': ALL}, 'nClicks'),
        Input('ai-chat-x-send-btn', 'nClicks'),
        Input('ai-chat-x-sse-completed-receiver', 'data-completion-event'),
        Input('voice-transcription-store-server', 'data')
    ],
    [
        State('ai-chat-x-input', 'value'),
        State('ai-chat-x-messages-store', 'data'),
        State('ai-chat-x-current-session-id', 'data'),
        State('voice-websocket-connection', 'data')
    ],
    prevent_initial_call=True
)
def handle_chat_interactions(...):
    triggered_id = ctx.triggered_id if ctx.triggered else None
    
    # Server-side validation (double-check after client-side)
    if triggered_id == 'ai-chat-x-send-btn':
        if not message_content or not message_content.strip():
            log.info('Empty input rejected on server side')
            return messages, message_content, False, False, dash.no_update
    
    # ... rest of existing business logic ...
    # SSE streaming, message storage, etc.
```

#### 6.2 SSE completion handling

Ensure SSE completion updates the appropriate stores for clientside callbacks to pick up.

### Phase 7: Testing & Validation (3 hours)

#### 7.1 Test Scenario 1: Text Chat

- Empty input → warning message, no state change
- Valid input → text_processing state, buttons update
- SSE streaming → maintains text_processing
- SSE complete with AUTO_PLAY=True → preparing_tts → playing_tts → idle
- SSE complete with AUTO_PLAY=False → directly to idle (skip TTS)
- Manual stop during TTS → idle

#### 7.2 Test Scenario 2: Voice Recording

- Start recording → recording state, red button
- Stop recording → voice_processing state, yellow button
- STT complete → text_processing state
- SSE complete → always plays TTS (ignore AUTO_PLAY)
- TTS complete → idle

#### 7.3 Test Edge Cases

- Rapid clicks (debounce)
- Network errors during SSE/STT/TTS
- WebSocket disconnection
- Page refresh during processing
- Multiple tabs/windows

#### 7.4 Performance Validation

- State transition latency < 50ms
- Button response time < 100ms
- No console errors
- No duplicate callback warnings
- Memory usage stable

### Phase 8: Documentation (1 hour)

#### 8.1 Update technical documentation

- Add architecture diagram showing Store-based flow
- Document state schema
- Document callback chain
- List all clientside callbacks and their purposes

#### 8.2 Add code comments

- Comment all callbacks with purpose
- Document state transition logic
- Add JSDoc to JavaScript methods

## Success Criteria

- ✅ All buttons use DashIconify/AntdIcon (no emoji)
- ✅ Buttons are unified: 40px × 40px, borderRadius 8px
- ✅ Central dcc.Store manages all button states
- ✅ Clientside callbacks handle all UI updates
- ✅ Server callbacks handle only business logic
- ✅ No duplicate callback output warnings
- ✅ TTS config works: check AUTO_PLAY for text chat, always play for voice recording
- ✅ Input validation works on both client and server
- ✅ State transitions are smooth and performant
- ✅ All tests pass with no console errors

## Key Differences from Previous Approach

1. **Store-Based State**: Single source of truth via dcc.Store
2. **Official Pattern**: Uses clientside_callback (official recommended) instead of pure set_props
3. **Separation**: Clear separation between state management (Store updates) and UI rendering (clientside callbacks)
4. **Reliability**: Store ensures state consistency, callbacks are triggered by Dash framework
5. **Debuggability**: State changes visible in Dash DevTools

### To-dos

- [ ] Create unified_button_state_manager.js with UnifiedButtonStateManager class, 7 global states, and button update methods
- [ ] Implement state transition methods including startTextProcessing, startRecording, stopRecording, sttCompleted, prepareForTTS, startPlayingTTS, stopPlayingOrComplete, resetToIdle
- [ ] Add TTS config control in prepareForTTS() to check AUTO_PLAY_DEFAULT and skip TTS when disabled (text chat only)
- [ ] Implement checkInputContent(), showInputEmptyWarning(), and handleTextButtonClick() for input validation
- [ ] Implement handleRecordButtonClick() and handleCallButtonClick() for button event handling
- [ ] Modify app.py layout to include unified_button_state_manager.js script before other voice scripts
- [ ] Integrate state manager into voice_recorder_enhanced.js for recording start, stop, and STT completion
- [ ] Integrate state manager into voice_player_enhanced.js for playback start, end, and error handling
- [ ] Add clientside callback in app.py for text button validation using state manager
- [ ] Add server-side input validation in chat_input_area_c.py handle_chat_interactions function
- [ ] Ensure SSE completion properly triggers prepareForTTS() which checks AUTO_PLAY config
- [ ] Test both scenarios (text chat and voice recording) including TTS config behavior and edge cases
- [ ] Add debouncing, minimize DOM updates, optimize logging, verify performance targets
- [ ] Update documentation with implementation notes, TTS config behavior, and testing results