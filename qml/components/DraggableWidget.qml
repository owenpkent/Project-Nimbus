import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root

    // Widget data from profile (set by CustomLayout)
    property string widgetId: ""
    property string widgetType: "button"   // "joystick", "button", "slider", "dpad", "wheel"
    property string widgetLabel: ""
    property int buttonId: 1
    property string widgetColor: "#333"
    property string widgetShape: "rounded" // "circle", "rounded", "square"
    property string orientation: "horizontal"
    property var mapping: ({})
    property bool centerReturn: false      // Slider: spring back to center on release
    property bool toggleMode: false        // Button: toggle vs momentary (per-widget override)

    // Edit mode toggle (controlled by parent CustomLayout)
    property bool editMode: false

    // Grid snap size
    property int gridSnap: 10

    // Minimum widget sizes
    readonly property int minWidth: (widgetType === "button") ? 40 : (widgetType === "dpad" ? 100 : 80)
    readonly property int minHeight: (widgetType === "button") ? 40 : (widgetType === "dpad" ? 100 : 80)

    // Signals
    signal widgetMoved(string wid, real wx, real wy)
    signal widgetResized(string wid, real ww, real wh)
    signal widgetRemoved(string wid)
    signal widgetConfigRequested(string wid)

    // Snap helper
    function snap(v) { return gridSnap > 0 ? Math.round(v / gridSnap) * gridSnap : v }

    // ==================== EDIT MODE OVERLAY ====================
    // Selection border when in edit mode
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: editMode ? "#4a9eff" : "transparent"
        border.width: editMode ? 2 : 0
        radius: 4
        z: 100
        visible: editMode

        // Drag handle (entire widget is draggable in edit mode)
        MouseArea {
            id: dragArea
            anchors.fill: parent
            enabled: editMode
            cursorShape: editMode ? Qt.SizeAllCursor : Qt.ArrowCursor
            drag.target: root
            drag.axis: Drag.XAndYAxis
            drag.minimumX: 0
            drag.minimumY: 0
            drag.maximumX: root.parent ? root.parent.width - root.width : 9999
            drag.maximumY: root.parent ? root.parent.height - root.height : 9999

            onReleased: {
                root.x = snap(root.x)
                root.y = snap(root.y)
                root.widgetMoved(root.widgetId, root.x, root.y)
            }

            onDoubleClicked: {
                root.widgetConfigRequested(root.widgetId)
            }
        }

        // Widget label in edit mode
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: -1
            width: editLabel.width + 10
            height: 18
            color: "#4a9eff"
            radius: 2
            z: 101

            Text {
                id: editLabel
                anchors.centerIn: parent
                text: root.widgetType.charAt(0).toUpperCase() + root.widgetType.slice(1) + (root.widgetLabel ? ": " + root.widgetLabel : "")
                color: "white"
                font.pixelSize: 10
                font.bold: true
            }
        }

        // Delete button (top-right corner)
        Rectangle {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: -6
            width: 20
            height: 20
            radius: 10
            color: deleteArea.containsMouse ? "#ff4444" : "#cc3333"
            z: 102

            Text {
                anchors.centerIn: parent
                text: "×"
                color: "white"
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                id: deleteArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.widgetRemoved(root.widgetId)
            }
        }

        // Resize handle (bottom-right corner)
        Rectangle {
            id: resizeHandle
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.margins: -4
            width: 14
            height: 14
            color: resizeArea.containsMouse ? "#4a9eff" : "#3a7acc"
            radius: 2
            z: 102

            Text {
                anchors.centerIn: parent
                text: "⇲"
                color: "white"
                font.pixelSize: 10
            }

            MouseArea {
                id: resizeArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.SizeFDiagCursor
                property real startX: 0
                property real startY: 0
                property real startW: 0
                property real startH: 0

                onPressed: function(mouse) {
                    startX = mouse.x + resizeHandle.x
                    startY = mouse.y + resizeHandle.y
                    startW = root.width
                    startH = root.height
                }

                onPositionChanged: function(mouse) {
                    if (!pressed) return
                    var dx = (mouse.x + resizeHandle.x) - startX
                    var dy = (mouse.y + resizeHandle.y) - startY
                    var newW = Math.max(root.minWidth, startW + dx)
                    var newH = Math.max(root.minHeight, startH + dy)
                    // Maintain square for joysticks and circle buttons
                    if (root.widgetType === "joystick" || root.widgetShape === "circle") {
                        var sz = Math.max(newW, newH)
                        root.width = snap(sz)
                        root.height = snap(sz)
                    } else {
                        root.width = snap(newW)
                        root.height = snap(newH)
                    }
                }

                onReleased: {
                    root.width = snap(root.width)
                    root.height = snap(root.height)
                    root.widgetResized(root.widgetId, root.width, root.height)
                }
            }
        }
    }

    // ==================== WIDGET CONTENT ====================
    // The actual interactive control rendered based on widgetType
    Loader {
        id: contentLoader
        anchors.fill: parent
        sourceComponent: {
            if (root.widgetType === "joystick") return joystickContent
            if (root.widgetType === "button") return buttonContent
            if (root.widgetType === "slider") return sliderContent
            if (root.widgetType === "dpad") return dpadContent
            if (root.widgetType === "wheel") return wheelContent
            return null
        }
        // Block mouse events to content when in edit mode (so drag works)
        enabled: !root.editMode
    }

    // ==================== JOYSTICK ====================
    Component {
        id: joystickContent

        Item {
            id: joyRoot
            property real xValue: 0
            property real yValue: 0
            property bool mouseLocked: false  // Triple-click lock state

            readonly property real borderWidth: 2
            readonly property real joyRadius: Math.max(1, Math.min(width, height) / 2 - borderWidth / 2)
            readonly property real thumbRadius: Math.min(width, height) * 0.18 * 0.5
            readonly property real effectiveRadius: Math.max(1, joyRadius - thumbRadius)
            readonly property real centerX: width / 2
            readonly property real centerY: height / 2

            property real _pressX: 0
            property real _pressY: 0
            property real _startXValue: 0
            property real _startYValue: 0

            // Triple-click detection
            property int _clickCount: 0
            property real _lastClickTime: 0

            function _checkTripleClick() {
                var now = Date.now()
                if (now - _lastClickTime < 400) {
                    _clickCount++
                } else {
                    _clickCount = 1
                }
                _lastClickTime = now
                if (_clickCount >= 3) {
                    _clickCount = 0
                    mouseLocked = !mouseLocked
                }
            }

            function _sendJoystickValues(nx, ny) {
                if (!controller) return
                var axisX = root.mapping["axis_x"] || ""
                var axisY = root.mapping["axis_y"] || ""
                if (axisX && axisY) {
                    if (axisX === "x" && axisY === "y") {
                        controller.setLeftStick(nx, -ny)
                    } else if (axisX === "rx" && axisY === "ry") {
                        controller.setRightStick(nx, -ny)
                    } else {
                        controller.setAxis(axisX, nx)
                        controller.setAxis(axisY, -ny)
                    }
                }
            }

            // Base circle
            Rectangle {
                width: joyRoot.joyRadius * 2
                height: width
                anchors.centerIn: parent
                radius: width / 2
                color: "#1e1e1e"
                border.color: joyRoot.mouseLocked ? "#ff6a00" : "#3d3d3d"
                border.width: joyRoot.borderWidth
            }

            // Thumb
            Rectangle {
                id: joyThumb
                width: Math.min(joyRoot.width, joyRoot.height) * 0.18
                height: width
                radius: width / 2
                color: joyRoot.mouseLocked ? "#d45500" : "#2e6bd1"
                border.color: joyRoot.mouseLocked ? "#ff8833" : "#6aa3ff"
                x: joyRoot.centerX + joyRoot.xValue * joyRoot.effectiveRadius - width / 2
                y: joyRoot.centerY + joyRoot.yValue * joyRoot.effectiveRadius - height / 2

                Behavior on x { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                Behavior on y { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            }

            // Lock indicator
            Text {
                anchors.top: parent.top
                anchors.topMargin: 4
                anchors.horizontalCenter: parent.horizontalCenter
                text: "LOCKED"
                color: "#ff6a00"
                font.pixelSize: 10
                font.bold: true
                visible: joyRoot.mouseLocked
            }

            // Label
            Text {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 4
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.widgetLabel
                color: "#666"
                font.pixelSize: 11
                visible: root.widgetLabel !== ""
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: joyRoot.mouseLocked

                onPressed: function(mouse) {
                    joyRoot._checkTripleClick()
                    joyRoot._pressX = mouse.x
                    joyRoot._pressY = mouse.y
                    joyRoot._startXValue = joyRoot.xValue
                    joyRoot._startYValue = joyRoot.yValue
                }
                onPositionChanged: function(mouse) {
                    // In locked mode, respond to hover; otherwise need press
                    if (!pressed && !joyRoot.mouseLocked) return
                    var dx = mouse.x - joyRoot._pressX
                    var dy = mouse.y - joyRoot._pressY
                    var nx, ny
                    if (joyRoot.mouseLocked) {
                        // In locked mode, map absolute position to joystick range
                        nx = ((mouse.x / width) * 2 - 1)
                        ny = ((mouse.y / height) * 2 - 1)
                    } else {
                        nx = joyRoot._startXValue + (dx / joyRoot.effectiveRadius)
                        ny = joyRoot._startYValue + (dy / joyRoot.effectiveRadius)
                    }
                    var mag2 = nx * nx + ny * ny
                    if (mag2 > 1.0) {
                        var mag = Math.sqrt(mag2)
                        nx /= mag
                        ny /= mag
                    }
                    joyRoot.xValue = nx
                    joyRoot.yValue = ny
                    joyRoot._sendJoystickValues(nx, ny)
                }
                onReleased: {
                    if (joyRoot.mouseLocked) return  // Don't release in locked mode
                    joyRoot.xValue = 0
                    joyRoot.yValue = 0
                    joyRoot._sendJoystickValues(0, 0)
                }
            }
        }
    }

    // ==================== BUTTON ====================
    Component {
        id: buttonContent

        Rectangle {
            id: btnRect
            property bool isPressed: false
            property bool isToggled: false

            radius: root.widgetShape === "circle" ? width / 2 : (root.widgetShape === "square" ? 4 : 8)
            color: {
                var base = root.widgetColor || "#333"
                if (isPressed || isToggled) return Qt.lighter(base, 1.4)
                if (btnMouseArea.containsMouse) return Qt.lighter(base, 1.2)
                return base
            }
            border.color: {
                if (isPressed || isToggled) return Qt.lighter(root.widgetColor || "#555", 1.6)
                return Qt.lighter(root.widgetColor || "#555", 1.3)
            }
            border.width: 3

            Text {
                anchors.centerIn: parent
                text: root.widgetLabel
                color: "white"
                font.pixelSize: Math.min(parent.width, parent.height) * 0.35
                font.bold: true
            }

            MouseArea {
                id: btnMouseArea
                anchors.fill: parent
                hoverEnabled: true
                onPressed: {
                    // Use per-widget toggleMode first, fall back to global config
                    var isToggle = root.toggleMode || (controller ? controller.isButtonToggle(root.buttonId) : false)
                    if (isToggle) {
                        btnRect.isToggled = !btnRect.isToggled
                        if (controller) controller.setButton(root.buttonId, btnRect.isToggled)
                    } else {
                        btnRect.isPressed = true
                        if (controller) controller.setButton(root.buttonId, true)
                    }
                }
                onReleased: {
                    var isToggle = root.toggleMode || (controller ? controller.isButtonToggle(root.buttonId) : false)
                    if (!isToggle) {
                        btnRect.isPressed = false
                        if (controller) controller.setButton(root.buttonId, false)
                    }
                }
            }
        }
    }

    // ==================== SLIDER ====================
    Component {
        id: sliderContent

        Rectangle {
            id: sliderRect
            color: "#252525"
            border.color: "#444"
            border.width: 2
            radius: 10

            // Label
            Text {
                id: sliderLabel
                anchors.top: parent.top
                anchors.topMargin: 4
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.widgetLabel
                color: "#aaa"
                font.pixelSize: 12
                font.bold: true
            }

            // Track
            Rectangle {
                id: sliderTrack
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 8
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - 16
                height: Math.max(20, parent.height - sliderLabel.height - 20)
                radius: 6
                color: "#1a1a1a"

                // Fill — changes behavior based on centerReturn
                Rectangle {
                    visible: !root.centerReturn
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * sliderDragArea.value
                    radius: 6
                    color: "#107c10"
                }

                // Center-return fill (shows deviation from center)
                Rectangle {
                    visible: root.centerReturn
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    x: sliderDragArea.value >= 0.5
                       ? parent.width / 2
                       : parent.width * sliderDragArea.value
                    width: Math.abs(sliderDragArea.value - 0.5) * parent.width
                    radius: 6
                    color: "#2e6bd1"
                }

                // Center line for center-return sliders
                Rectangle {
                    visible: root.centerReturn
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    x: parent.width / 2 - 1
                    width: 2
                    color: "#666"
                }

                MouseArea {
                    id: sliderDragArea
                    property real value: root.centerReturn ? 0.5 : 0
                    anchors.fill: parent
                    onPositionChanged: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        _sendSliderValue(value)
                    }
                    onPressed: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        _sendSliderValue(value)
                    }
                    onReleased: {
                        if (root.centerReturn) {
                            // Spring back to center
                            value = 0.5
                            _sendSliderValue(0.5)
                        } else {
                            // Keep at current position (throttle-like)
                        }
                    }

                    function _sendSliderValue(v) {
                        if (!controller) return
                        var axis = root.mapping["axis"] || ""
                        if (root.centerReturn) {
                            // Center-return: 0.5 = center (0), 0 = -1, 1 = +1
                            var normalized = (v - 0.5) * 2  // -1 to +1
                            if (axis !== "") controller.setAxis(axis, normalized)
                        } else {
                            // One-way: 0 = min, 1 = max
                            if (axis === "z") {
                                controller.setThrottle(v)
                            } else if (axis === "rz") {
                                controller.setRudder(v * 2 - 1)
                            } else if (axis !== "") {
                                controller.setAxis(axis, v * 2 - 1)
                            }
                        }
                    }
                }
            }
        }
    }

    // ==================== D-PAD ====================
    Component {
        id: dpadContent

        Item {
            id: dpadRoot
            readonly property real btnSize: Math.min(width, height) * 0.35
            readonly property real gap: 2
            readonly property real cx: width / 2
            readonly property real cy: height / 2

            function _pressDir(dir, pressed) {
                if (!controller) return
                var m = root.mapping || {}
                var btnId = m[dir] || 0
                if (btnId > 0) controller.setButton(btnId, pressed)
            }

            // Up
            Rectangle {
                x: dpadRoot.cx - dpadRoot.btnSize / 2
                y: dpadRoot.cy - dpadRoot.btnSize - dpadRoot.gap - dpadRoot.btnSize / 2
                width: dpadRoot.btnSize; height: dpadRoot.btnSize
                radius: 4; color: dpadUp.pressed ? "#4a9eff" : "#333"
                border.color: "#555"; border.width: 1
                Text { anchors.centerIn: parent; text: "\u25B2"; color: "white"; font.pixelSize: dpadRoot.btnSize * 0.4 }
                MouseArea { id: dpadUp; anchors.fill: parent
                    onPressed: dpadRoot._pressDir("up", true)
                    onReleased: dpadRoot._pressDir("up", false)
                }
            }
            // Down
            Rectangle {
                x: dpadRoot.cx - dpadRoot.btnSize / 2
                y: dpadRoot.cy + dpadRoot.gap + dpadRoot.btnSize / 2
                width: dpadRoot.btnSize; height: dpadRoot.btnSize
                radius: 4; color: dpadDown.pressed ? "#4a9eff" : "#333"
                border.color: "#555"; border.width: 1
                Text { anchors.centerIn: parent; text: "\u25BC"; color: "white"; font.pixelSize: dpadRoot.btnSize * 0.4 }
                MouseArea { id: dpadDown; anchors.fill: parent
                    onPressed: dpadRoot._pressDir("down", true)
                    onReleased: dpadRoot._pressDir("down", false)
                }
            }
            // Left
            Rectangle {
                x: dpadRoot.cx - dpadRoot.btnSize - dpadRoot.gap - dpadRoot.btnSize / 2
                y: dpadRoot.cy - dpadRoot.btnSize / 2
                width: dpadRoot.btnSize; height: dpadRoot.btnSize
                radius: 4; color: dpadLeft.pressed ? "#4a9eff" : "#333"
                border.color: "#555"; border.width: 1
                Text { anchors.centerIn: parent; text: "\u25C0"; color: "white"; font.pixelSize: dpadRoot.btnSize * 0.4 }
                MouseArea { id: dpadLeft; anchors.fill: parent
                    onPressed: dpadRoot._pressDir("left", true)
                    onReleased: dpadRoot._pressDir("left", false)
                }
            }
            // Right
            Rectangle {
                x: dpadRoot.cx + dpadRoot.gap + dpadRoot.btnSize / 2
                y: dpadRoot.cy - dpadRoot.btnSize / 2
                width: dpadRoot.btnSize; height: dpadRoot.btnSize
                radius: 4; color: dpadRight.pressed ? "#4a9eff" : "#333"
                border.color: "#555"; border.width: 1
                Text { anchors.centerIn: parent; text: "\u25B6"; color: "white"; font.pixelSize: dpadRoot.btnSize * 0.4 }
                MouseArea { id: dpadRight; anchors.fill: parent
                    onPressed: dpadRoot._pressDir("right", true)
                    onReleased: dpadRoot._pressDir("right", false)
                }
            }
            // Center cross
            Rectangle {
                x: dpadRoot.cx - dpadRoot.btnSize / 2; y: dpadRoot.cy - dpadRoot.btnSize / 2
                width: dpadRoot.btnSize; height: dpadRoot.btnSize
                radius: 4; color: "#222"; border.color: "#444"; border.width: 1
            }
            // Label
            Text {
                anchors.bottom: parent.bottom; anchors.bottomMargin: 2
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.widgetLabel; color: "#666"; font.pixelSize: 10
                visible: root.widgetLabel !== ""
            }
        }
    }

    // ==================== STEERING WHEEL ====================
    Component {
        id: wheelContent

        Item {
            id: wheelRoot
            property real angle: 0  // -1 to +1

            readonly property real wheelRadius: Math.min(width, height) / 2 - 6
            readonly property real cx: width / 2
            readonly property real cy: height / 2

            // Outer ring
            Rectangle {
                anchors.centerIn: parent
                width: wheelRoot.wheelRadius * 2; height: width
                radius: width / 2
                color: "transparent"
                border.color: "#555"; border.width: 4
            }

            // Inner ring
            Rectangle {
                anchors.centerIn: parent
                width: wheelRoot.wheelRadius * 1.4; height: width
                radius: width / 2
                color: "transparent"
                border.color: "#333"; border.width: 2
            }

            // Rotation indicator (spoke)
            Rectangle {
                id: wheelSpoke
                width: 6; height: wheelRoot.wheelRadius * 0.8
                radius: 3
                color: "#2e6bd1"
                x: wheelRoot.cx - 3
                y: wheelRoot.cy - wheelRoot.wheelRadius * 0.8
                transformOrigin: Item.Bottom
                rotation: wheelRoot.angle * 135  // ±135 degrees visual range

                Behavior on rotation { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            }

            // Center hub
            Rectangle {
                anchors.centerIn: parent
                width: 16; height: 16; radius: 8
                color: "#444"; border.color: "#666"; border.width: 1
            }

            // Label
            Text {
                anchors.bottom: parent.bottom; anchors.bottomMargin: 2
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.widgetLabel; color: "#666"; font.pixelSize: 10
                visible: root.widgetLabel !== ""
            }

            MouseArea {
                anchors.fill: parent
                property real _pressX: 0

                onPressed: function(mouse) { _pressX = mouse.x }
                onPositionChanged: function(mouse) {
                    if (!pressed) return
                    // Map horizontal drag to -1..+1
                    var raw = ((mouse.x / width) * 2 - 1)
                    wheelRoot.angle = Math.max(-1, Math.min(1, raw))
                    if (controller) {
                        var axis = root.mapping["axis"] || ""
                        if (axis !== "") controller.setAxis(axis, wheelRoot.angle)
                    }
                }
                onReleased: {
                    // Spring to center
                    wheelRoot.angle = 0
                    if (controller) {
                        var axis = root.mapping["axis"] || ""
                        if (axis !== "") controller.setAxis(axis, 0)
                    }
                }
            }
        }
    }
}
