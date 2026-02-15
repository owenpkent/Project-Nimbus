import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "../components" as Comp

Item {
    id: root
    property real scaleFactor: 1.0

    // Edit mode state
    property bool editMode: false
    property bool showGrid: true
    property int gridSnap: 10

    // Joystick mouse-lock tracking
    property string lockedJoystickId: ""
    property var lockedWidget: null

    // Widget model - loaded from profile via bridge
    property var widgetModel: []

    // Load layout from bridge on creation
    Component.onCompleted: {
        if (controller) {
            var data = controller.getCustomLayout()
            if (data && data.length > 0) {
                widgetModel = JSON.parse(data)
                gridSnap = controller.getCustomLayoutGridSnap()
                showGrid = controller.getCustomLayoutShowGrid()
            }
        }
    }

    // ==================== CANVAS BACKGROUND ====================
    Rectangle {
        id: canvas
        anchors.fill: parent
        color: "#111111"
        clip: true

        // Grid overlay
        Canvas {
            id: gridCanvas
            anchors.fill: parent
            visible: editMode && showGrid
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "#222222"
                ctx.lineWidth = 0.5

                var step = root.gridSnap > 0 ? root.gridSnap : 10

                // Vertical lines
                for (var x = 0; x <= width; x += step) {
                    ctx.beginPath()
                    ctx.moveTo(x, 0)
                    ctx.lineTo(x, height)
                    ctx.stroke()
                }
                // Horizontal lines
                for (var y = 0; y <= height; y += step) {
                    ctx.beginPath()
                    ctx.moveTo(0, y)
                    ctx.lineTo(width, y)
                    ctx.stroke()
                }
            }
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onVisibleChanged: requestPaint()
        }

        // Edit mode instruction banner
        Rectangle {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 8
            width: editBannerText.width + 30
            height: 28
            radius: 14
            color: "#333"
            border.color: "#4a9eff"
            border.width: 1
            visible: editMode
            z: 200

            Text {
                id: editBannerText
                anchors.centerIn: parent
                text: "Edit Mode — Drag to move, corner to resize, double-click to configure"
                color: "#4a9eff"
                font.pixelSize: 11
                font.bold: true
            }
        }

        // ==================== WIDGET REPEATER ====================
        Repeater {
            id: widgetRepeater
            model: root.widgetModel

            Comp.DraggableWidget {
                id: dragWidget

                // Pull data from model
                property var wData: modelData || {}

                x: wData.x || 0
                y: wData.y || 0
                width: wData.width || 100
                height: wData.height || 100

                widgetId: wData.id || ""
                widgetType: wData.type || "button"
                widgetLabel: wData.label || ""
                buttonId: wData.button_id || 1
                widgetColor: wData.color || "#333"
                widgetShape: wData.shape || "rounded"
                orientation: wData.orientation || "horizontal"
                mapping: wData.mapping || {}
                snapMode: wData.snap_mode || "none"
                clickMode: wData.click_mode || "jump"
                toggleMode: wData.toggle_mode || false
                tripleClickEnabled: wData.triple_click_enabled !== undefined ? wData.triple_click_enabled : true
                sensitivity: wData.sensitivity !== undefined ? wData.sensitivity : 50.0
                deadZone: wData.dead_zone !== undefined ? wData.dead_zone : 0.0
                extremityDeadZone: wData.extremity_dead_zone !== undefined ? wData.extremity_dead_zone : 5.0

                editMode: root.editMode
                gridSnap: root.gridSnap

                onWidgetMoved: function(wid, wx, wy) {
                    root._updateWidgetProp(wid, "x", wx)
                    root._updateWidgetProp(wid, "y", wy)
                    root._autoSave()
                }

                onWidgetResized: function(wid, ww, wh) {
                    root._updateWidgetProp(wid, "width", ww)
                    root._updateWidgetProp(wid, "height", wh)
                    root._autoSave()
                }

                onWidgetRemoved: function(wid) {
                    root._removeWidget(wid)
                    root._autoSave()
                }

                onWidgetConfigRequested: function(wid) {
                    configDialog.openForWidget(wid)
                }

                onMouseLockChanged: function(wid, locked) {
                    if (locked) {
                        root.lockedJoystickId = wid
                        root.lockedWidget = dragWidget
                    } else {
                        root.lockedJoystickId = ""
                        root.lockedWidget = null
                    }
                }
            }
        }
    }

    // ==================== MOUSE LOCK OVERLAY ====================
    // Full-canvas hover overlay that tracks mouse when a joystick is locked
    MouseArea {
        id: joyLockOverlay
        anchors.fill: parent
        visible: root.lockedJoystickId !== "" && !root.editMode
        hoverEnabled: true
        z: 200

        onPositionChanged: function(mouse) {
            if (!root.lockedWidget) return
            var localPt = mapToItem(root.lockedWidget, mouse.x, mouse.y)
            var nx = ((localPt.x / root.lockedWidget.width) * 2 - 1)
            var ny = ((localPt.y / root.lockedWidget.height) * 2 - 1)
            root.lockedWidget.updateJoystickPosition(nx, ny)
        }

        onClicked: function(mouse) {
            if (root.lockedWidget) {
                root.lockedWidget.triggerTripleClick()
            }
        }
    }

    // ==================== WIDGET PALETTE (pop-out tool window) ====================
    Window {
        id: paletteWindow
        title: "Widget Palette"
        width: 190
        height: 680
        visible: root.editMode
        flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            color: "#2a2a2a"
            border.color: "#4a9eff"
            border.width: 1
            radius: 8

            // Custom draggable title bar
            Rectangle {
                id: paletteTitleBar
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 28
                color: paletteDragArea.containsPress ? "#1a5a9e" : "#1e3a5a"
                radius: 8

                // Square off bottom corners
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 8
                    color: parent.color
                }

                Text {
                    anchors.centerIn: parent
                    text: "Widget Palette"
                    color: "#ccc"
                    font.pixelSize: 12
                    font.bold: true
                }

                MouseArea {
                    id: paletteDragArea
                    anchors.fill: parent
                    property real _startX: 0
                    property real _startY: 0
                    property bool containsPress: pressed

                    onPressed: function(mouse) {
                        _startX = mouse.x
                        _startY = mouse.y
                    }
                    onPositionChanged: function(mouse) {
                        if (!pressed) return
                        paletteWindow.x += (mouse.x - _startX)
                        paletteWindow.y += (mouse.y - _startY)
                    }
                }
            }

            Comp.WidgetPalette {
                id: widgetPalette
                anchors.top: paletteTitleBar.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 2
                editMode: root.editMode
                widgetModel: root.widgetModel

                onAddWidget: function(widgetData) {
                    root._addWidget(widgetData)
                    _autoSave()
                }

                onSaveLayout: {
                    root._saveLayout()
                }

                onToggleGrid: {
                    root.showGrid = !root.showGrid
                    gridCanvas.requestPaint()
                }

                onDoneEditing: {
                    root.editMode = false
                    root._saveLayout()
                }

                onSaveLayoutAs: function(layoutName) {
                    saveAsDialog.visible = true
                    saveAsNameField.text = ""
                    saveAsNameField.forceActiveFocus()
                }
            }
        }
    }

    // ==================== EDIT MODE TOGGLE BUTTON (play mode only) ====================
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 12
        width: editToggleRow.width + 20
        height: 36
        radius: 18
        color: "#333"
        border.color: "#555"
        border.width: 1
        z: 300
        visible: !root.editMode

        Row {
            id: editToggleRow
            anchors.centerIn: parent
            spacing: 6

            Text {
                text: "\u270F"
                color: "white"
                font.pixelSize: 14
            }
            Text {
                text: "Edit Layout"
                color: "white"
                font.pixelSize: 12
                font.bold: true
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                root.editMode = true
            }
        }
    }

    // ==================== WIDGET CONFIG DIALOG ====================
    Rectangle {
        id: configDialog
        anchors.centerIn: parent
        width: 360
        height: Math.min(configContent.height + 60, root.height - 40)
        radius: 12
        color: "#2a2a2a"
        border.color: "#4a9eff"
        border.width: 2
        visible: false
        z: 500
        clip: true

        property string targetWidgetId: ""
        property var targetWidget: null

        function openForWidget(wid) {
            for (var i = 0; i < root.widgetModel.length; i++) {
                if (root.widgetModel[i].id === wid) {
                    targetWidgetId = wid
                    targetWidget = root.widgetModel[i]
                    labelField.text = targetWidget.label || ""

                    // Sensitivity & deadzone (all axis types, percentage-based)
                    sensitivitySlider.value = targetWidget.sensitivity !== undefined ? targetWidget.sensitivity : 50.0
                    deadZoneSlider.value = targetWidget.dead_zone !== undefined ? targetWidget.dead_zone : 0.0
                    extremityDzSlider.value = targetWidget.extremity_dead_zone !== undefined ? targetWidget.extremity_dead_zone : 5.0

                    if (targetWidget.type === "button") {
                        buttonIdField.text = String(targetWidget.button_id || 1)
                        colorField.text = targetWidget.color || "#333"
                        shapeCombo.currentIndex = ["circle", "rounded", "square"].indexOf(targetWidget.shape || "rounded")
                        toggleModeSwitch.checked = targetWidget.toggle_mode || false
                    }
                    if (targetWidget.type === "joystick") {
                        var axPair = (targetWidget.mapping.axis_x || "x") + "/" + (targetWidget.mapping.axis_y || "y")
                        axisPairCombo.currentIndex = ["x/y", "rx/ry", "z/rz", "sl0/sl1"].indexOf(axPair)
                        if (axisPairCombo.currentIndex < 0) axisPairCombo.currentIndex = 0
                        tripleClickSwitch.checked = targetWidget.triple_click_enabled !== undefined ? targetWidget.triple_click_enabled : true
                    }
                    if (targetWidget.type === "slider" || targetWidget.type === "wheel") {
                        var slAxis = targetWidget.mapping.axis || "z"
                        sliderAxisCombo.currentIndex = ["z", "rz", "sl0", "sl1", "x", "y", "rx", "ry"].indexOf(slAxis)
                        if (sliderAxisCombo.currentIndex < 0) sliderAxisCombo.currentIndex = 0
                        if (targetWidget.type === "slider") {
                            snapModeCombo.currentIndex = ["none", "left", "center"].indexOf(targetWidget.snap_mode || "none")
                            if (snapModeCombo.currentIndex < 0) snapModeCombo.currentIndex = 0
                            clickModeCombo.currentIndex = ["jump", "relative"].indexOf(targetWidget.click_mode || "jump")
                            if (clickModeCombo.currentIndex < 0) clickModeCombo.currentIndex = 0
                        }
                    }
                    if (targetWidget.type === "dpad") {
                        dpadUpIdField.text = String(targetWidget.mapping.up || 1)
                        dpadDownIdField.text = String(targetWidget.mapping.down || 2)
                        dpadLeftIdField.text = String(targetWidget.mapping.left || 3)
                        dpadRightIdField.text = String(targetWidget.mapping.right || 4)
                    }
                    visible = true
                    return
                }
            }
        }

        // Dim background
        Rectangle {
            parent: root
            anchors.fill: parent
            color: "#00000088"
            visible: configDialog.visible
            z: 499

            MouseArea {
                anchors.fill: parent
                onClicked: configDialog.visible = false
            }
        }

        Flickable {
            id: configFlickable
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: dialogButtonRow.top
            anchors.margins: 10
            contentHeight: configContent.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick

        Column {
            id: configContent
            width: configFlickable.width
            spacing: 10

            Text {
                text: "Configure Widget"
                color: "#fff"
                font.pixelSize: 16
                font.bold: true
            }

            Rectangle { width: parent.width; height: 1; color: "#444" }

            // Label
            Row {
                spacing: 8
                Text { text: "Label:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                Rectangle {
                    width: 200; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                    TextInput {
                        id: labelField
                        anchors.fill: parent
                        anchors.margins: 6
                        color: "white"
                        font.pixelSize: 12
                    }
                }
            }

            // Button-specific fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? configDialog.targetWidget.type === "button" : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Button ID:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 80; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput {
                            id: buttonIdField
                            anchors.fill: parent
                            anchors.margins: 6
                            color: "white"
                            font.pixelSize: 12
                            validator: IntValidator { bottom: 1; top: 128 }
                        }
                    }
                    Text { text: "(1-128)"; color: "#888"; font.pixelSize: 10; verticalAlignment: Text.AlignVCenter; height: 30 }
                }

                Row {
                    spacing: 8
                    Text { text: "Color:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 120; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput {
                            id: colorField
                            anchors.fill: parent
                            anchors.margins: 6
                            color: "white"
                            font.pixelSize: 12
                        }
                    }
                    Rectangle {
                        width: 30; height: 30; radius: 4
                        color: colorField.text || "#333"
                        border.color: "#666"
                        border.width: 1
                    }
                }

                Row {
                    spacing: 8
                    Text { text: "Shape:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: shapeCombo
                        width: 120
                        model: ["circle", "rounded", "square"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: shapeCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: shapeCombo.width
                            highlighted: shapeCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                        }
                        popup: Popup {
                            y: shapeCombo.height; width: shapeCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: shapeCombo.delegateModel; currentIndex: shapeCombo.highlightedIndex }
                        }
                    }
                }

                // Toggle mode
                Row {
                    spacing: 8
                    Text { text: "Mode:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 180; height: 30; radius: 4; color: "transparent"
                        Row {
                            spacing: 8
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                id: toggleModeSwitch
                                property bool checked: false
                                width: 44; height: 22; radius: 11
                                color: checked ? "#16a34a" : "#555"
                                Rectangle {
                                    width: 18; height: 18; radius: 9
                                    color: "white"
                                    x: parent.checked ? parent.width - width - 2 : 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 120 } }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: parent.checked = !parent.checked
                                }
                            }
                            Text {
                                text: toggleModeSwitch.checked ? "Toggle" : "Momentary"
                                color: toggleModeSwitch.checked ? "#4ade80" : "#aaa"
                                font.pixelSize: 11
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }

            // Joystick-specific fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? configDialog.targetWidget.type === "joystick" : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Axis Pair:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: axisPairCombo
                        width: 200
                        model: ["x/y (Left Stick)", "rx/ry (Right Stick)", "z/rz (Throttle/Rudder)", "sl0/sl1 (Slider Axes)"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: axisPairCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: axisPairCombo.width
                            highlighted: axisPairCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                        }
                        popup: Popup {
                            y: axisPairCombo.height; width: axisPairCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: axisPairCombo.delegateModel; currentIndex: axisPairCombo.highlightedIndex }
                        }
                    }
                }

                // Triple-click lock toggle
                Row {
                    spacing: 8
                    Text { text: "Lock:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 200; height: 30; radius: 4; color: "transparent"
                        Row {
                            spacing: 8
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                id: tripleClickSwitch
                                property bool checked: true
                                width: 44; height: 22; radius: 11
                                color: checked ? "#d45500" : "#555"
                                Rectangle {
                                    width: 18; height: 18; radius: 9; color: "white"
                                    x: parent.checked ? parent.width - width - 2 : 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 120 } }
                                }
                                MouseArea { anchors.fill: parent; onClicked: parent.checked = !parent.checked }
                            }
                            Text {
                                text: tripleClickSwitch.checked ? "Triple-click lock ON" : "Triple-click lock OFF"
                                color: tripleClickSwitch.checked ? "#ff8833" : "#aaa"
                                font.pixelSize: 11
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }

            // D-Pad specific fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? configDialog.targetWidget.type === "dpad" : false
                width: parent.width

                Text { text: "Button IDs (1-128):"; color: "#aaa"; font.pixelSize: 11; font.bold: true }

                Row {
                    spacing: 8
                    Text { text: "Up:"; color: "#ccc"; font.pixelSize: 12; width: 50; verticalAlignment: Text.AlignVCenter; height: 28 }
                    Rectangle {
                        width: 50; height: 28; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput { id: dpadUpIdField; anchors.fill: parent; anchors.margins: 4; color: "white"; font.pixelSize: 12; validator: IntValidator { bottom: 1; top: 128 } }
                    }
                    Text { text: "Down:"; color: "#ccc"; font.pixelSize: 12; width: 50; verticalAlignment: Text.AlignVCenter; height: 28 }
                    Rectangle {
                        width: 50; height: 28; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput { id: dpadDownIdField; anchors.fill: parent; anchors.margins: 4; color: "white"; font.pixelSize: 12; validator: IntValidator { bottom: 1; top: 128 } }
                    }
                }
                Row {
                    spacing: 8
                    Text { text: "Left:"; color: "#ccc"; font.pixelSize: 12; width: 50; verticalAlignment: Text.AlignVCenter; height: 28 }
                    Rectangle {
                        width: 50; height: 28; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput { id: dpadLeftIdField; anchors.fill: parent; anchors.margins: 4; color: "white"; font.pixelSize: 12; validator: IntValidator { bottom: 1; top: 128 } }
                    }
                    Text { text: "Right:"; color: "#ccc"; font.pixelSize: 12; width: 50; verticalAlignment: Text.AlignVCenter; height: 28 }
                    Rectangle {
                        width: 50; height: 28; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput { id: dpadRightIdField; anchors.fill: parent; anchors.margins: 4; color: "white"; font.pixelSize: 12; validator: IntValidator { bottom: 1; top: 128 } }
                    }
                }
            }

            // Slider & Wheel axis fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? (configDialog.targetWidget.type === "slider" || configDialog.targetWidget.type === "wheel") : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Axis:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: sliderAxisCombo
                        width: 200
                        model: ["z (LT/Throttle)", "rz (RT/Rudder)", "sl0 (Slider 0)", "sl1 (Slider 1)", "x", "y", "rx", "ry"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: sliderAxisCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: sliderAxisCombo.width
                            highlighted: sliderAxisCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                        }
                        popup: Popup {
                            y: sliderAxisCombo.height; width: sliderAxisCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: sliderAxisCombo.delegateModel; currentIndex: sliderAxisCombo.highlightedIndex }
                        }
                    }
                }

                // Snap mode (slider only)
                Row {
                    spacing: 8
                    visible: configDialog.targetWidget ? configDialog.targetWidget.type === "slider" : false
                    Text { text: "Snap:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: snapModeCombo
                        width: 200
                        model: ["None (hold position)", "Snap to zero", "Snap to center"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: snapModeCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: snapModeCombo.width
                            highlighted: snapModeCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                        }
                        popup: Popup {
                            y: snapModeCombo.height; width: snapModeCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: snapModeCombo.delegateModel; currentIndex: snapModeCombo.highlightedIndex }
                        }
                    }
                }

                // Click mode (slider only)
                Row {
                    spacing: 8
                    visible: configDialog.targetWidget ? configDialog.targetWidget.type === "slider" : false
                    Text { text: "Click:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: clickModeCombo
                        width: 200
                        model: ["Jump to position", "Relative drag"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: clickModeCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: clickModeCombo.width
                            highlighted: clickModeCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                        }
                        popup: Popup {
                            y: clickModeCombo.height; width: clickModeCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: clickModeCombo.delegateModel; currentIndex: clickModeCombo.highlightedIndex }
                        }
                    }
                }

                // Orientation display (read-only, set by widget type from palette)
                Row {
                    spacing: 8
                    visible: configDialog.targetWidget ? configDialog.targetWidget.type === "slider" : false
                    Text { text: "Orient:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Text {
                        text: configDialog.targetWidget ? (configDialog.targetWidget.orientation === "vertical" ? "Vertical" : "Horizontal") : "Horizontal"
                        color: "#aaa"; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter; height: 30
                    }
                }
            }

            // Sensitivity & Deadzone (for axis widgets: joystick, slider, wheel)
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? (configDialog.targetWidget.type === "joystick" || configDialog.targetWidget.type === "slider" || configDialog.targetWidget.type === "wheel") : false
                width: parent.width

                Rectangle { width: parent.width; height: 1; color: "#444" }

                Text { text: "Sensitivity Settings"; color: "#aaa"; font.pixelSize: 11; font.bold: true }

                // Sensitivity slider (0-100%, 50% = linear)
                Row {
                    spacing: 8
                    Text { text: "Sensitivity:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.Slider {
                        id: sensitivitySlider
                        width: 140
                        from: 0; to: 100; stepSize: 1
                        value: 50
                        onValueChanged: responseCurve.requestPaint()
                        background: Rectangle {
                            x: sensitivitySlider.leftPadding; y: sensitivitySlider.topPadding + sensitivitySlider.availableHeight / 2 - height / 2
                            width: sensitivitySlider.availableWidth; height: 4; radius: 2; color: "#444"
                            Rectangle { width: sensitivitySlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#4a9eff" }
                        }
                        handle: Rectangle { x: sensitivitySlider.leftPadding + sensitivitySlider.visualPosition * (sensitivitySlider.availableWidth - width); y: sensitivitySlider.topPadding + sensitivitySlider.availableHeight / 2 - height / 2; width: 16; height: 16; radius: 8; color: "#fff" }
                    }
                    Text { text: sensitivitySlider.value.toFixed(0) + "%"; color: "#4a9eff"; font.pixelSize: 11; width: 35; verticalAlignment: Text.AlignVCenter; height: 30 }
                }

                // Dead zone slider (0-100%)
                Row {
                    spacing: 8
                    Text { text: "Deadzone:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.Slider {
                        id: deadZoneSlider
                        width: 140
                        from: 0; to: 100; stepSize: 1
                        value: 0
                        onValueChanged: responseCurve.requestPaint()
                        background: Rectangle {
                            x: deadZoneSlider.leftPadding; y: deadZoneSlider.topPadding + deadZoneSlider.availableHeight / 2 - height / 2
                            width: deadZoneSlider.availableWidth; height: 4; radius: 2; color: "#444"
                            Rectangle { width: deadZoneSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#ff6a00" }
                        }
                        handle: Rectangle { x: deadZoneSlider.leftPadding + deadZoneSlider.visualPosition * (deadZoneSlider.availableWidth - width); y: deadZoneSlider.topPadding + deadZoneSlider.availableHeight / 2 - height / 2; width: 16; height: 16; radius: 8; color: "#fff" }
                    }
                    Text { text: deadZoneSlider.value.toFixed(0) + "%"; color: "#ff6a00"; font.pixelSize: 11; width: 35; verticalAlignment: Text.AlignVCenter; height: 30 }
                }

                // Extremity dead zone slider (0-100%)
                Row {
                    spacing: 8
                    Text { text: "Extremity:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.Slider {
                        id: extremityDzSlider
                        width: 140
                        from: 0; to: 100; stepSize: 1
                        value: 5
                        onValueChanged: responseCurve.requestPaint()
                        background: Rectangle {
                            x: extremityDzSlider.leftPadding; y: extremityDzSlider.topPadding + extremityDzSlider.availableHeight / 2 - height / 2
                            width: extremityDzSlider.availableWidth; height: 4; radius: 2; color: "#444"
                            Rectangle { width: extremityDzSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#aa44ff" }
                        }
                        handle: Rectangle { x: extremityDzSlider.leftPadding + extremityDzSlider.visualPosition * (extremityDzSlider.availableWidth - width); y: extremityDzSlider.topPadding + extremityDzSlider.availableHeight / 2 - height / 2; width: 16; height: 16; radius: 8; color: "#fff" }
                    }
                    Text { text: extremityDzSlider.value.toFixed(0) + "%"; color: "#aa44ff"; font.pixelSize: 11; width: 35; verticalAlignment: Text.AlignVCenter; height: 30 }
                }

                // Response Curve Preview (matches Settings menu graph exactly)
                Text { text: "Response Curve Preview"; color: "#888"; font.pixelSize: 10 }
                Rectangle {
                    width: parent.width; height: 120
                    color: "#111"; border.color: "#444"; border.width: 1; radius: 4

                    Canvas {
                        id: responseCurve
                        anchors.fill: parent
                        anchors.margins: 4
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            var w = width, h = height
                            // Convert from percentage to internal units (same as config.py)
                            var sens = sensitivitySlider.value / 100.0     // 0..1
                            var dz = (deadZoneSlider.value / 100.0) * 0.25 // 0..0.25
                            var edz = extremityDzSlider.value / 100.0      // 0..1

                            // Grid lines
                            ctx.strokeStyle = "#333"
                            ctx.lineWidth = 0.5
                            for (var g = 0; g <= 4; g++) {
                                var gx = w * g / 4
                                ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke()
                                var gy = h * g / 4
                                ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke()
                            }

                            // Dead zone shaded region
                            if (dz > 0) {
                                ctx.fillStyle = "rgba(255,106,0,0.15)"
                                ctx.fillRect(0, 0, w * dz, h)
                            }

                            // Curve (exact same formula as apply_joystick_dialog_curve)
                            ctx.strokeStyle = "#4a9eff"
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            var first = true
                            for (var i = 0; i <= 100; i++) {
                                var input = i / 100.0
                                var output
                                if (input < dz) {
                                    output = 0
                                } else {
                                    var availRange = 1.0 - dz
                                    var normalized = availRange > 0 ? (input - dz) / availRange : 1
                                    if (Math.abs(sens - 0.5) < 1e-9) {
                                        output = normalized
                                    } else if (sens < 0.5) {
                                        var power = 1.0 + (0.5 - sens) * 6.0
                                        output = Math.pow(normalized, power)
                                    } else {
                                        var power2 = 1.0 - (sens - 0.5) * 1.8
                                        output = Math.pow(normalized, Math.max(0.1, power2))
                                    }
                                    if (edz > 0) output *= (1.0 - edz)
                                }
                                var px = i / 100.0 * w
                                var py = h - output * h
                                if (first) { ctx.moveTo(px, py); first = false }
                                else ctx.lineTo(px, py)
                            }
                            ctx.stroke()

                            // Linear reference line (dashed)
                            ctx.strokeStyle = "#555"
                            ctx.lineWidth = 1
                            ctx.setLineDash([4, 4])
                            ctx.beginPath(); ctx.moveTo(0, h); ctx.lineTo(w, 0); ctx.stroke()
                            ctx.setLineDash([])
                        }
                    }
                }
            }

        }
        }  // close Flickable

        // Dialog buttons — always visible at bottom, outside Flickable
        Row {
            id: dialogButtonRow
            spacing: 10
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.margins: 12

            Rectangle {
                width: 70; height: 32; radius: 6
                color: cancelConfigArea.containsMouse ? "#444" : "#333"
                border.color: "#555"
                Text { anchors.centerIn: parent; text: "Cancel"; color: "#ccc"; font.pixelSize: 12 }
                MouseArea { id: cancelConfigArea; anchors.fill: parent; hoverEnabled: true; onClicked: configDialog.visible = false }
            }

            Rectangle {
                width: 70; height: 32; radius: 6
                color: applyConfigArea.containsMouse ? "#1a8cff" : "#0078d4"
                Text { anchors.centerIn: parent; text: "Apply"; color: "white"; font.pixelSize: 12; font.bold: true }
                MouseArea {
                    id: applyConfigArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        var wid = configDialog.targetWidgetId
                        var wType = configDialog.targetWidget.type
                        _updateWidgetProp(wid, "label", labelField.text)

                        if (wType === "button") {
                            _updateWidgetProp(wid, "button_id", parseInt(buttonIdField.text) || 1)
                            _updateWidgetProp(wid, "color", colorField.text)
                            _updateWidgetProp(wid, "shape", shapeCombo.currentText)
                            _updateWidgetProp(wid, "toggle_mode", toggleModeSwitch.checked)
                        }

                        if (wType === "joystick") {
                            var axisPairs = [["x", "y"], ["rx", "ry"], ["z", "rz"], ["sl0", "sl1"]]
                            var pair = axisPairs[axisPairCombo.currentIndex] || ["x", "y"]
                            _updateWidgetProp(wid, "mapping", {"axis_x": pair[0], "axis_y": pair[1]})
                            _updateWidgetProp(wid, "triple_click_enabled", tripleClickSwitch.checked)
                        }

                        if (wType === "slider" || wType === "wheel") {
                            var sliderAxes = ["z", "rz", "sl0", "sl1", "x", "y", "rx", "ry"]
                            _updateWidgetProp(wid, "mapping", {"axis": sliderAxes[sliderAxisCombo.currentIndex] || "z"})
                            if (wType === "slider") {
                                var snapModes = ["none", "left", "center"]
                                _updateWidgetProp(wid, "snap_mode", snapModes[snapModeCombo.currentIndex] || "none")
                                var clickModes = ["jump", "relative"]
                                _updateWidgetProp(wid, "click_mode", clickModes[clickModeCombo.currentIndex] || "jump")
                            }
                        }

                        if (wType === "dpad") {
                            _updateWidgetProp(wid, "mapping", {
                                "up": parseInt(dpadUpIdField.text) || 1,
                                "down": parseInt(dpadDownIdField.text) || 2,
                                "left": parseInt(dpadLeftIdField.text) || 3,
                                "right": parseInt(dpadRightIdField.text) || 4
                            })
                        }

                        // Save sensitivity & deadzone for axis widgets
                        if (wType === "joystick" || wType === "slider" || wType === "wheel") {
                            _updateWidgetProp(wid, "sensitivity", sensitivitySlider.value)
                            _updateWidgetProp(wid, "dead_zone", deadZoneSlider.value)
                            _updateWidgetProp(wid, "extremity_dead_zone", extremityDzSlider.value)
                        }

                        configDialog.visible = false
                        // Force model refresh — deep copy creates new objects so Repeater recreates delegates
                        root.widgetModel = JSON.parse(JSON.stringify(root.widgetModel))
                        _autoSave()
                    }
                }
            }
        }
    }

    // ==================== SAVE AS DIALOG ====================
    Rectangle {
        id: saveAsDialog
        anchors.centerIn: parent
        width: 320
        height: saveAsContent.height + 20
        radius: 12
        color: "#2a2a2a"
        border.color: "#4a9eff"
        border.width: 2
        visible: false
        z: 510

        // Dim background
        Rectangle {
            parent: root
            anchors.fill: parent
            color: "#00000088"
            visible: saveAsDialog.visible
            z: 509
            MouseArea { anchors.fill: parent; onClicked: saveAsDialog.visible = false }
        }

        Column {
            id: saveAsContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 16
            spacing: 12

            Text { text: "Save Layout As..."; color: "#fff"; font.pixelSize: 16; font.bold: true }
            Text { text: "Enter a name for this layout (e.g. game name):"; color: "#aaa"; font.pixelSize: 11 }

            Rectangle {
                width: parent.width; height: 34; radius: 4; color: "#1a1a1a"; border.color: "#444"
                TextInput {
                    id: saveAsNameField
                    anchors.fill: parent
                    anchors.margins: 8
                    color: "white"
                    font.pixelSize: 13
                }
            }

            Row {
                spacing: 10
                anchors.right: parent.right

                Rectangle {
                    width: 70; height: 32; radius: 6
                    color: saveAsCancelArea.containsMouse ? "#444" : "#333"
                    border.color: "#555"
                    Text { anchors.centerIn: parent; text: "Cancel"; color: "#ccc"; font.pixelSize: 12 }
                    MouseArea { id: saveAsCancelArea; anchors.fill: parent; hoverEnabled: true; onClicked: saveAsDialog.visible = false }
                }

                Rectangle {
                    width: 70; height: 32; radius: 6
                    color: saveAsOkArea.containsMouse ? "#1a8cff" : "#0078d4"
                    Text { anchors.centerIn: parent; text: "Save"; color: "white"; font.pixelSize: 12; font.bold: true }
                    MouseArea {
                        id: saveAsOkArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            var name = saveAsNameField.text.trim()
                            if (name.length > 0 && controller) {
                                controller.saveCustomLayoutAs(name, JSON.stringify(root.widgetModel), root.gridSnap, root.showGrid)
                            }
                            saveAsDialog.visible = false
                        }
                    }
                }
            }
        }
    }

    // ==================== HELPER FUNCTIONS ====================
    function _updateWidgetProp(wid, prop, value) {
        for (var i = 0; i < widgetModel.length; i++) {
            if (widgetModel[i].id === wid) {
                widgetModel[i][prop] = value
                return
            }
        }
    }

    function _addWidget(data) {
        var m = widgetModel.slice()
        m.push(data)
        widgetModel = m
    }

    function _removeWidget(wid) {
        var m = []
        for (var i = 0; i < widgetModel.length; i++) {
            if (widgetModel[i].id !== wid) {
                m.push(widgetModel[i])
            }
        }
        widgetModel = m
    }

    function _saveLayout() {
        if (controller) {
            controller.saveCustomLayout(JSON.stringify(widgetModel), gridSnap, showGrid)
        }
    }

    function _autoSave() {
        if (controller && editMode) {
            controller.saveCustomLayout(JSON.stringify(widgetModel), gridSnap, showGrid)
        }
    }
}
