import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 480
    height: 560
    radius: 12
    color: "#2a2a2a"
    border.color: "#e040fb"
    border.width: 2

    property var macroConfig: ({
        "zones": {
            "north": { "action": "none" },
            "northeast": { "action": "none" },
            "east": { "action": "none" },
            "southeast": { "action": "none" },
            "south": { "action": "none" },
            "southwest": { "action": "none" },
            "west": { "action": "none" },
            "northwest": { "action": "none" },
            "center": { "action": "none" }
        },
        "deadzone_percent": 30,
        "diagonal_mode": "8-way"
    })

    property string selectedZone: "north"

    signal applyRequested(var config)
    signal cancelRequested()

    // Zone labels for display
    readonly property var zoneLabels: ({
        "north": "↑ North",
        "northeast": "↗ NE",
        "east": "→ East",
        "southeast": "↘ SE",
        "south": "↓ South",
        "southwest": "↙ SW",
        "west": "← West",
        "northwest": "↖ NW",
        "center": "● Center"
    })

    // Action type labels
    readonly property var actionLabels: ["None", "Button", "Multi-Button", "Axis", "Turbo"]

    function loadConfig(cfg) {
        if (cfg && cfg.zones) {
            macroConfig = JSON.parse(JSON.stringify(cfg))
        }
        selectedZone = "north"
        _refreshZoneEditor()
    }

    function _getZoneConfig(zone) {
        return macroConfig.zones[zone] || { "action": "none" }
    }

    function _setZoneConfig(zone, cfg) {
        if (!macroConfig.zones) macroConfig.zones = {}
        macroConfig.zones[zone] = cfg
    }

    function _refreshZoneEditor() {
        var cfg = _getZoneConfig(selectedZone)
        actionCombo.currentIndex = ["none", "button", "multi_button", "axis", "turbo"].indexOf(cfg.action || "none")
        if (actionCombo.currentIndex < 0) actionCombo.currentIndex = 0

        // Button fields
        buttonIdField.text = cfg.buttons && cfg.buttons.length > 0 ? String(cfg.buttons[0]) : "1"

        // Multi-button fields
        multiButtonField.text = cfg.buttons ? cfg.buttons.join(", ") : ""

        // Axis fields
        axisCombo.currentIndex = ["x", "y", "rx", "ry", "z", "rz", "sl0", "sl1"].indexOf(cfg.axis || "x")
        if (axisCombo.currentIndex < 0) axisCombo.currentIndex = 0
        axisValueSlider.value = cfg.axis_value !== undefined ? cfg.axis_value : 1.0

        // Turbo fields
        turboButtonField.text = cfg.buttons && cfg.buttons.length > 0 ? String(cfg.buttons[0]) : "1"
        turboHzSlider.value = cfg.turbo_hz || 10
    }

    function _saveCurrentZone() {
        var cfg = { "action": ["none", "button", "multi_button", "axis", "turbo"][actionCombo.currentIndex] }

        if (cfg.action === "button") {
            cfg.buttons = [parseInt(buttonIdField.text) || 1]
        } else if (cfg.action === "multi_button") {
            var parts = multiButtonField.text.split(",").map(function(s) { return parseInt(s.trim()) }).filter(function(n) { return !isNaN(n) && n > 0 })
            cfg.buttons = parts.length > 0 ? parts : [1]
        } else if (cfg.action === "axis") {
            cfg.axis = ["x", "y", "rx", "ry", "z", "rz", "sl0", "sl1"][axisCombo.currentIndex]
            cfg.axis_value = axisValueSlider.value
        } else if (cfg.action === "turbo") {
            cfg.buttons = [parseInt(turboButtonField.text) || 1]
            cfg.turbo_hz = turboHzSlider.value
        }

        _setZoneConfig(selectedZone, cfg)
    }

    // Title
    Text {
        id: titleText
        anchors.top: parent.top
        anchors.topMargin: 12
        anchors.horizontalCenter: parent.horizontalCenter
        text: "Macro Joystick Editor"
        color: "#e040fb"
        font.pixelSize: 16
        font.bold: true
    }

    // Divider
    Rectangle {
        id: titleDivider
        anchors.top: titleText.bottom
        anchors.topMargin: 8
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 24
        height: 1
        color: "#444"
    }

    // Main content area
    Row {
        id: mainContent
        anchors.top: titleDivider.bottom
        anchors.topMargin: 12
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 12
        spacing: 16

        // Left: Visual joystick zone selector
        Item {
            width: 180
            height: 180

            // Zone visualization
            Canvas {
                id: zoneCanvas
                anchors.fill: parent

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)

                    var cx = width / 2
                    var cy = height / 2
                    var r = Math.min(width, height) / 2 - 4

                    // Draw outer circle
                    ctx.strokeStyle = "#555"
                    ctx.lineWidth = 2
                    ctx.beginPath()
                    ctx.arc(cx, cy, r, 0, Math.PI * 2)
                    ctx.stroke()

                    // Draw zone lines
                    ctx.strokeStyle = "#333"
                    ctx.lineWidth = 1
                    for (var i = 0; i < 8; i++) {
                        var angle = (i * 45 - 90 + 22.5) * Math.PI / 180
                        ctx.beginPath()
                        ctx.moveTo(cx + r * 0.3 * Math.cos(angle), cy + r * 0.3 * Math.sin(angle))
                        ctx.lineTo(cx + r * Math.cos(angle), cy + r * Math.sin(angle))
                        ctx.stroke()
                    }

                    // Draw center circle
                    ctx.strokeStyle = "#444"
                    ctx.beginPath()
                    ctx.arc(cx, cy, r * 0.3, 0, Math.PI * 2)
                    ctx.stroke()
                }
            }

            // Zone buttons (clickable areas)
            Repeater {
                model: [
                    { zone: "north", angle: -90, dist: 0.65 },
                    { zone: "northeast", angle: -45, dist: 0.65 },
                    { zone: "east", angle: 0, dist: 0.65 },
                    { zone: "southeast", angle: 45, dist: 0.65 },
                    { zone: "south", angle: 90, dist: 0.65 },
                    { zone: "southwest", angle: 135, dist: 0.65 },
                    { zone: "west", angle: 180, dist: 0.65 },
                    { zone: "northwest", angle: -135, dist: 0.65 }
                ]

                Rectangle {
                    property var zoneData: modelData
                    property real angleRad: zoneData.angle * Math.PI / 180
                    property real cx: parent.width / 2
                    property real cy: parent.height / 2
                    property real r: Math.min(parent.width, parent.height) / 2 - 4

                    x: cx + r * zoneData.dist * Math.cos(angleRad) - width / 2
                    y: cy + r * zoneData.dist * Math.sin(angleRad) - height / 2
                    width: 28
                    height: 28
                    radius: 14
                    color: root.selectedZone === zoneData.zone ? "#e040fb" : (_getZoneConfig(zoneData.zone).action !== "none" ? "#6a1b9a" : "#333")
                    border.color: root.selectedZone === zoneData.zone ? "#fff" : "#555"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: {
                            var dirs = { "north": "↑", "northeast": "↗", "east": "→", "southeast": "↘",
                                        "south": "↓", "southwest": "↙", "west": "←", "northwest": "↖" }
                            return dirs[zoneData.zone] || "?"
                        }
                        color: "white"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            _saveCurrentZone()
                            root.selectedZone = zoneData.zone
                            _refreshZoneEditor()
                        }
                    }
                }
            }

            // Center zone button
            Rectangle {
                anchors.centerIn: parent
                width: 36
                height: 36
                radius: 18
                color: root.selectedZone === "center" ? "#e040fb" : (_getZoneConfig("center").action !== "none" ? "#6a1b9a" : "#333")
                border.color: root.selectedZone === "center" ? "#fff" : "#555"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "●"
                    color: "white"
                    font.pixelSize: 16
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        _saveCurrentZone()
                        root.selectedZone = "center"
                        _refreshZoneEditor()
                    }
                }
            }
        }

        // Right: Zone configuration editor
        Rectangle {
            width: 250
            height: 180
            radius: 8
            color: "#1a1a1a"
            border.color: "#444"

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                // Zone name
                Text {
                    text: zoneLabels[root.selectedZone] || root.selectedZone
                    color: "#e040fb"
                    font.pixelSize: 14
                    font.bold: true
                }

                Rectangle { width: parent.width; height: 1; color: "#333" }

                // Action type
                Row {
                    spacing: 8
                    Text { text: "Action:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                    Basic.ComboBox {
                        id: actionCombo
                        width: 140
                        height: 28
                        model: root.actionLabels
                        onCurrentIndexChanged: _saveCurrentZone()
                        background: Rectangle { color: "#252525"; border.color: "#555"; radius: 4 }
                        contentItem: Text { text: actionCombo.displayText; color: "white"; font.pixelSize: 11; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        delegate: ItemDelegate {
                            width: actionCombo.width
                            highlighted: actionCombo.highlightedIndex === index
                            contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 11; leftPadding: 8 }
                            background: Rectangle { color: parent.highlighted ? "#e040fb" : "#333" }
                        }
                        popup: Popup {
                            y: actionCombo.height; width: actionCombo.width; padding: 1
                            background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: actionCombo.delegateModel; currentIndex: actionCombo.highlightedIndex }
                        }
                    }
                }

                // Button action fields
                Row {
                    spacing: 8
                    visible: actionCombo.currentIndex === 1
                    Text { text: "Button:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                    Rectangle {
                        width: 60; height: 26; radius: 4; color: "#252525"; border.color: "#555"
                        TextInput {
                            id: buttonIdField
                            anchors.fill: parent; anchors.margins: 4
                            color: "white"; font.pixelSize: 11
                            validator: IntValidator { bottom: 1; top: 128 }
                            onTextChanged: _saveCurrentZone()
                        }
                    }
                    Text { text: "(1-128)"; color: "#888"; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter }
                }

                // Multi-button action fields
                Column {
                    spacing: 4
                    visible: actionCombo.currentIndex === 2
                    Row {
                        spacing: 8
                        Text { text: "Buttons:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                        Rectangle {
                            width: 140; height: 26; radius: 4; color: "#252525"; border.color: "#555"
                            TextInput {
                                id: multiButtonField
                                anchors.fill: parent; anchors.margins: 4
                                color: "white"; font.pixelSize: 11
                                onTextChanged: _saveCurrentZone()
                            }
                        }
                    }
                    Text { text: "Comma-separated IDs (e.g., 1, 2, 5)"; color: "#666"; font.pixelSize: 9; leftPadding: 58 }
                }

                // Axis action fields
                Column {
                    spacing: 4
                    visible: actionCombo.currentIndex === 3
                    Row {
                        spacing: 8
                        Text { text: "Axis:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                        Basic.ComboBox {
                            id: axisCombo
                            width: 80; height: 26
                            model: ["X", "Y", "RX", "RY", "Z", "RZ", "SL0", "SL1"]
                            onCurrentIndexChanged: _saveCurrentZone()
                            background: Rectangle { color: "#252525"; border.color: "#555"; radius: 4 }
                            contentItem: Text { text: axisCombo.displayText; color: "white"; font.pixelSize: 11; leftPadding: 6; verticalAlignment: Text.AlignVCenter }
                            delegate: ItemDelegate {
                                width: axisCombo.width
                                highlighted: axisCombo.highlightedIndex === index
                                contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 11; leftPadding: 6 }
                                background: Rectangle { color: parent.highlighted ? "#e040fb" : "#333" }
                            }
                            popup: Popup {
                                y: axisCombo.height
                                width: axisCombo.width
                                padding: 1
                                background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                                contentItem: ListView { clip: true; implicitHeight: contentHeight; model: axisCombo.delegateModel }
                            }
                        }
                    }
                    Row {
                        spacing: 8
                        Text { text: "Value:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                        Basic.Slider {
                            id: axisValueSlider
                            width: 100; from: -1; to: 1; stepSize: 0.1; value: 1.0
                            onValueChanged: _saveCurrentZone()
                            background: Rectangle { x: axisValueSlider.leftPadding; y: axisValueSlider.topPadding + axisValueSlider.availableHeight / 2 - 2; width: axisValueSlider.availableWidth; height: 4; radius: 2; color: "#444"
                                Rectangle { width: axisValueSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#e040fb" }
                            }
                            handle: Rectangle { x: axisValueSlider.leftPadding + axisValueSlider.visualPosition * (axisValueSlider.availableWidth - width); y: axisValueSlider.topPadding + axisValueSlider.availableHeight / 2 - height / 2; width: 14; height: 14; radius: 7; color: "#fff" }
                        }
                        Text { text: axisValueSlider.value.toFixed(1); color: "#e040fb"; font.pixelSize: 10; width: 30; anchors.verticalCenter: parent.verticalCenter }
                    }
                }

                // Turbo action fields
                Column {
                    spacing: 4
                    visible: actionCombo.currentIndex === 4
                    Row {
                        spacing: 8
                        Text { text: "Button:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                        Rectangle {
                            width: 60; height: 26; radius: 4; color: "#252525"; border.color: "#555"
                            TextInput {
                                id: turboButtonField
                                anchors.fill: parent; anchors.margins: 4
                                color: "white"; font.pixelSize: 11
                                validator: IntValidator { bottom: 1; top: 128 }
                                onTextChanged: _saveCurrentZone()
                            }
                        }
                    }
                    Row {
                        spacing: 8
                        Text { text: "Rate:"; color: "#ccc"; font.pixelSize: 11; width: 50; anchors.verticalCenter: parent.verticalCenter }
                        Basic.Slider {
                            id: turboHzSlider
                            width: 100; from: 1; to: 30; stepSize: 1; value: 10
                            onValueChanged: _saveCurrentZone()
                            background: Rectangle { x: turboHzSlider.leftPadding; y: turboHzSlider.topPadding + turboHzSlider.availableHeight / 2 - 2; width: turboHzSlider.availableWidth; height: 4; radius: 2; color: "#444"
                                Rectangle { width: turboHzSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#ff9800" }
                            }
                            handle: Rectangle { x: turboHzSlider.leftPadding + turboHzSlider.visualPosition * (turboHzSlider.availableWidth - width); y: turboHzSlider.topPadding + turboHzSlider.availableHeight / 2 - height / 2; width: 14; height: 14; radius: 7; color: "#fff" }
                        }
                        Text { text: turboHzSlider.value.toFixed(0) + " Hz"; color: "#ff9800"; font.pixelSize: 10; width: 40; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
            }
        }
    }

    // Settings section
    Rectangle {
        id: settingsSection
        anchors.top: mainContent.bottom
        anchors.topMargin: 16
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 12
        height: 80
        radius: 8
        color: "#1a1a1a"
        border.color: "#444"

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Text { text: "Macro Settings"; color: "#aaa"; font.pixelSize: 12; font.bold: true }

            Row {
                spacing: 12
                Text { text: "Deadzone:"; color: "#ccc"; font.pixelSize: 11; width: 70; anchors.verticalCenter: parent.verticalCenter }
                Basic.Slider {
                    id: deadzoneSlider
                    width: 140; from: 10; to: 50; stepSize: 5; value: root.macroConfig.deadzone_percent || 30
                    onValueChanged: root.macroConfig.deadzone_percent = value
                    background: Rectangle { x: deadzoneSlider.leftPadding; y: deadzoneSlider.topPadding + deadzoneSlider.availableHeight / 2 - 2; width: deadzoneSlider.availableWidth; height: 4; radius: 2; color: "#444"
                        Rectangle { width: deadzoneSlider.visualPosition * parent.width; height: parent.height; radius: 2; color: "#4a9eff" }
                    }
                    handle: Rectangle { x: deadzoneSlider.leftPadding + deadzoneSlider.visualPosition * (deadzoneSlider.availableWidth - width); y: deadzoneSlider.topPadding + deadzoneSlider.availableHeight / 2 - height / 2; width: 14; height: 14; radius: 7; color: "#fff" }
                }
                Text { text: deadzoneSlider.value.toFixed(0) + "%"; color: "#4a9eff"; font.pixelSize: 11; width: 40; anchors.verticalCenter: parent.verticalCenter }
            }

            Row {
                spacing: 12
                Text { text: "Mode:"; color: "#ccc"; font.pixelSize: 11; width: 70; anchors.verticalCenter: parent.verticalCenter }
                Basic.ComboBox {
                    id: diagonalModeCombo
                    width: 120; height: 26
                    model: ["4-Way", "8-Way"]
                    currentIndex: root.macroConfig.diagonal_mode === "4-way" ? 0 : 1
                    onCurrentIndexChanged: root.macroConfig.diagonal_mode = currentIndex === 0 ? "4-way" : "8-way"
                    background: Rectangle { color: "#252525"; border.color: "#555"; radius: 4 }
                    contentItem: Text { text: diagonalModeCombo.displayText; color: "white"; font.pixelSize: 11; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                    delegate: ItemDelegate {
                        width: diagonalModeCombo.width
                        highlighted: diagonalModeCombo.highlightedIndex === index
                        contentItem: Text { text: modelData; color: parent.highlighted ? "white" : "#ccc"; font.pixelSize: 11; leftPadding: 8 }
                        background: Rectangle { color: parent.highlighted ? "#4a9eff" : "#333" }
                    }
                    popup: Popup {
                        y: diagonalModeCombo.height
                        width: diagonalModeCombo.width
                        padding: 1
                        background: Rectangle { color: "#333"; border.color: "#555"; radius: 4 }
                        contentItem: ListView { clip: true; implicitHeight: contentHeight; model: diagonalModeCombo.delegateModel }
                    }
                }
                Text { text: diagonalModeCombo.currentIndex === 0 ? "(cardinal only)" : "(diagonals enabled)"; color: "#888"; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }

    // Preset buttons section
    Rectangle {
        id: presetsSection
        anchors.top: settingsSection.bottom
        anchors.topMargin: 12
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 12
        height: 100
        radius: 8
        color: "#1a1a1a"
        border.color: "#444"

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Text { text: "Quick Presets"; color: "#aaa"; font.pixelSize: 12; font.bold: true }

            Flow {
                width: parent.width
                spacing: 8

                Repeater {
                    model: [
                        { name: "ABXY", preset: "abxy" },
                        { name: "D-Pad", preset: "dpad" },
                        { name: "Triggers", preset: "triggers" },
                        { name: "Shoulders", preset: "shoulders" },
                        { name: "Clear All", preset: "clear" }
                    ]

                    Rectangle {
                        width: 70; height: 28; radius: 4
                        color: presetMa.containsMouse ? "#444" : "#333"
                        border.color: "#555"

                        Text {
                            anchors.centerIn: parent
                            text: modelData.name
                            color: modelData.preset === "clear" ? "#ff6b6b" : "#ccc"
                            font.pixelSize: 10
                            font.bold: true
                        }

                        MouseArea {
                            id: presetMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root._applyPreset(modelData.preset)
                        }
                    }
                }
            }
        }
    }

    function _applyPreset(preset) {
        var zones = {}
        var allZones = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest", "center"]
        for (var i = 0; i < allZones.length; i++) {
            zones[allZones[i]] = { "action": "none" }
        }

        if (preset === "abxy") {
            zones.north = { action: "button", buttons: [4] }    // Y
            zones.east = { action: "button", buttons: [2] }     // B
            zones.south = { action: "button", buttons: [1] }    // A
            zones.west = { action: "button", buttons: [3] }     // X
        } else if (preset === "dpad") {
            zones.north = { action: "button", buttons: [13] }   // D-Up
            zones.east = { action: "button", buttons: [16] }    // D-Right
            zones.south = { action: "button", buttons: [14] }   // D-Down
            zones.west = { action: "button", buttons: [15] }    // D-Left
        } else if (preset === "triggers") {
            zones.north = { action: "axis", axis: "z", axis_value: 1.0 }     // LT
            zones.south = { action: "axis", axis: "rz", axis_value: 1.0 }    // RT
        } else if (preset === "shoulders") {
            zones.west = { action: "button", buttons: [5] }     // LB
            zones.east = { action: "button", buttons: [6] }     // RB
            zones.center = { action: "button", buttons: [9] }   // LS
        }

        macroConfig.zones = zones
        _refreshZoneEditor()
    }

    // Button row
    Row {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 12
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 16

        Rectangle {
            width: 100; height: 36; radius: 6
            color: applyMa.containsMouse ? "#7b1fa2" : "#6a1b9a"

            Text { anchors.centerIn: parent; text: "Apply"; color: "white"; font.pixelSize: 13; font.bold: true }

            MouseArea {
                id: applyMa
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    _saveCurrentZone()
                    root.applyRequested(root.macroConfig)
                }
            }
        }

        Rectangle {
            width: 100; height: 36; radius: 6
            color: cancelMa.containsMouse ? "#555" : "#444"

            Text { anchors.centerIn: parent; text: "Cancel"; color: "#ccc"; font.pixelSize: 13; font.bold: true }

            MouseArea {
                id: cancelMa
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.cancelRequested()
            }
        }
    }
}
