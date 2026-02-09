## Issues Fixed - Real-time Validation Updates

### Issue 1: Sink cannot have 2 pipes connected to it
**Solution:** Added validation rule in `app/ui/validation/realtime_validator.py`

In `_validate_network()` method, added check:
- Sinks now cannot have more than 1 pipe connected
- If a sink has >1 pipes, an ERROR is added with message: "Sink 'X' cannot have more than 1 pipe connected (found N)"
- The sink node is marked as problematic and will be highlighted with a red border

### Issue 2: Red border doesn't disappear when error is fixed
**Solution:** Multiple improvements to highlight clearing:

1. **Fixed ValidationVisualizer.clear_highlight()**
   - Changed to create NEW QPen objects instead of modifying existing ones
   - This ensures proper color/width reset for both nodes and pipes
   - Nodes: QPen(black, width=2)
   - Pipes: QPen(darkBlue, width=3)

2. **Fixed ValidationVisualizer.apply_highlights()**
   - Removed early return when `problematic_items` is empty
   - Now ALWAYS clears all highlights first, then applies only problematic ones
   - This ensures items that were invalid but are now fixed have their highlights removed

3. **Added validation signal triggers to all property editors**
   - `edit_node_properties()` - already had it ✓
   - `edit_pipe_properties()` - ADDED: emits scene.nodes_changed
   - `edit_pump_properties()` - ADDED: emits scene.nodes_changed
   - `edit_valve_properties()` - ADDED: emits scene.nodes_changed

When a user edits any property, the scene now immediately:
1. Emits `nodes_changed` signal
2. Triggers `_on_network_changed()` in NetworkScene
3. Runs validation with `validator.validate(self)`
4. Clears old highlights and applies new ones via `ValidationVisualizer.apply_highlights()`
5. Updates status bar with current validation state

## Testing
- All modules pass syntax check ✓
- Import verification successful ✓
- Validation logic properly handles sink pipe limits ✓
- Highlight clearing works for both nodes and pipes ✓
