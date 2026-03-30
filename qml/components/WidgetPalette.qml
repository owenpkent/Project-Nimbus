import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: palette
    color: "#2a2a2a"
    border.color: "#444"
    border.width: 1
    radius: 8
    // visibility controlled by parent (Window or inline)

    property bool editMode: false
    property int gridSnap: 10
    property var widgetModel: []  // Current widgets for smart assignment
    property string outputMode: "vjoy"  // "vjoy" or "vigem"

    // Signals to parent
    signal addWidget(var widgetData)
    signal saveLayout()
    signal toggleGrid()
    signal doneEditing()
    signal saveLayoutAs(string layoutName)

    readonly property var xboxButtons: [
        { "id": 1,  "label": "A",     "color": "#1a7a1a" },
        { "id": 2,  "label": "B",     "color": "#7a1a1a" },
        { "id": 3,  "label": "X",     "color": "#1a3a7a" },
        { "id": 4,  "label": "Y",     "color": "#7a7a1a" },
        { "id": 5,  "label": "LB",    "color": "#444444" },
        { "id": 6,  "label": "RB",    "color": "#444444" },
        { "id": 7,  "label": "Back",  "color": "#333333" },
        { "id": 8,  "label": "Start", "color": "#333333" },
        { "id": 9,  "label": "LS",    "color": "#555555" },
        { "id": 10, "label": "RS",    "color": "#555555" }
    ]

    // Check if all axis pairs are used
    function _allAxisPairsUsed() {
        var usedPairs = 0
        for (var i = 0; i < widgetModel.length; i++) {
            var w = widgetModel[i]
            if (w.mapping && w.mapping.axis_x && w.mapping.axis_y) usedPairs++
        }
        return usedPairs >= 4  // 4 pairs: x/y, rx/ry, z/rz, sl0/sl1
    }

    // Check if all single axes are used
    function _allSingleAxesUsed() {
        var usedAxes = {}
        for (var i = 0; i < widgetModel.length; i++) {
            var w = widgetModel[i]
            if (w.mapping) {
                if (w.mapping.axis) usedAxes[w.mapping.axis] = true
                if (w.mapping.axis_x) { usedAxes[w.mapping.axis_x] = true; usedAxes[w.mapping.axis_y] = true }
            }
        }
        return Object.keys(usedAxes).length >= 8  // 8 axes total
    }

    // Find next unused button ID by scanning existing widgets
    function _nextButtonId() {
        var used = {}
        for (var i = 0; i < widgetModel.length; i++) {
            var w = widgetModel[i]
            if (w.button_id) used[w.button_id] = true
            // Also check dpad mappings
            if (w.mapping) {
                if (w.mapping.up) used[w.mapping.up] = true
                if (w.mapping.down) used[w.mapping.down] = true
                if (w.mapping.left) used[w.mapping.left] = true
                if (w.mapping.right) used[w.mapping.right] = true
            }
        }
        for (var id = 1; id <= 128; id++) {
            if (!used[id]) return id
        }
        return 1
    }

    // Find next unused axis pair for joystick
    function _nextAxisPair() {
        var usedPairs = {}
        for (var i = 0; i < widgetModel.length; i++) {
            var w = widgetModel[i]
            if (w.mapping && w.mapping.axis_x && w.mapping.axis_y) {
                usedPairs[w.mapping.axis_x + "/" + w.mapping.axis_y] = true
            }
        }
        var pairs = [["x","y"],["rx","ry"],["z","rz"],["sl0","sl1"]]
        for (var j = 0; j < pairs.length; j++) {
            var key = pairs[j][0] + "/" + pairs[j][1]
            if (!usedPairs[key]) return {"axis_x": pairs[j][0], "axis_y": pairs[j][1]}
        }
        return {"axis_x": "x", "axis_y": "y"}
    }

    // Find next unused single axis for slider/wheel
    function _nextSingleAxis() {
        var usedAxes = {}
        for (var i = 0; i < widgetModel.length; i++) {
            var w = widgetModel[i]
            if (w.mapping) {
                if (w.mapping.axis) usedAxes[w.mapping.axis] = true
                if (w.mapping.axis_x) usedAxes[w.mapping.axis_x] = true
                if (w.mapping.axis_y) usedAxes[w.mapping.axis_y] = true
            }
        }
        var axes = ["z", "rz", "sl0", "sl1", "x", "y", "rx", "ry"]
        for (var j = 0; j < axes.length; j++) {
            if (!usedAxes[axes[j]]) return axes[j]
        }
        return "z"
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 8
        contentHeight: paletteColumn.implicitHeight
        clip: true
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { id: vsb; policy: ScrollBar.AsNeeded }

    ColumnLayout {
        id: paletteColumn
        width: parent.width - vsb.width
        spacing: 10

        // Add Joystick (vJoy only — generic, auto-picks next axis pair)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode !== "vigem"
            color: joyAddArea.containsMouse ? "#3a5a8a" : "#2e4a6e"
            border.color: "#4a7aaa"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "◉"; color: "#6aa3ff"; font.pixelSize: 16 }
                Text { text: "Joystick"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: joyAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "joystick_" + Date.now()
                    var axes = palette._nextAxisPair()
                    palette.addWidget({
                        "id": uid,
                        "type": "joystick",
                        "x": 100,
                        "y": 200,
                        "width": 180,
                        "height": 180,
                        "label": "Stick",
                        "mapping": axes
                    })
                }
            }
        }

        // Left Stick (ViGEm only — x/y)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode === "vigem"
            color: lStickArea.containsMouse ? "#3a5a8a" : "#2e4a6e"
            border.color: "#4a7aaa"
            border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 6
                Text { text: "◉"; color: "#6aa3ff"; font.pixelSize: 16 }
                Text { text: "Left Stick"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }
            MouseArea {
                id: lStickArea; anchors.fill: parent; hoverEnabled: true
                onClicked: palette.addWidget({ "id": "joystick_" + Date.now(), "type": "joystick",
                    "x": 80, "y": 200, "width": 180, "height": 180, "label": "Left Stick",
                    "mapping": {"axis_x": "x", "axis_y": "y"} })
            }
        }

        // Right Stick (ViGEm only — rx/ry)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode === "vigem"
            color: rStickArea.containsMouse ? "#3a5a8a" : "#2e4a6e"
            border.color: "#4a7aaa"
            border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 6
                Text { text: "◉"; color: "#6aa3ff"; font.pixelSize: 16 }
                Text { text: "Right Stick"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }
            MouseArea {
                id: rStickArea; anchors.fill: parent; hoverEnabled: true
                onClicked: palette.addWidget({ "id": "joystick_" + Date.now(), "type": "joystick",
                    "x": 300, "y": 200, "width": 180, "height": 180, "label": "Right Stick",
                    "mapping": {"axis_x": "rx", "axis_y": "ry"} })
            }
        }

        // Add Button (generic — vJoy only; Xbox users use the presets below)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode !== "vigem"
            color: btnAddArea.containsMouse ? "#5a3a3a" : "#4e2e2e"
            border.color: "#aa4a4a"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "●"; color: "#ff6a6a"; font.pixelSize: 16 }
                Text { text: "Button"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: btnAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var nextId = palette._nextButtonId()
                    var uid = "button_" + Date.now()
                    palette.addWidget({
                        "id": uid,
                        "type": "button",
                        "x": 400,
                        "y": 300,
                        "width": 60,
                        "height": 60,
                        "label": "B" + nextId,
                        "button_id": nextId,
                        "color": "#333333",
                        "shape": "circle",
                        "toggle_mode": false
                    })
                }
            }
        }

        // Xbox Button Presets (visible when ViGEm output selected)
        Column {
            Layout.fillWidth: true
            spacing: 5
            visible: palette.outputMode === "vigem"

            Text {
                text: "Xbox Buttons:"
                color: "#aaa"
                font.pixelSize: 11
                font.bold: true
                bottomPadding: 4
                topPadding: 2
            }

            // Grid of Xbox button presets
            Grid {
                columns: 2
                spacing: 5
                width: parent.width

                Repeater {
                    model: palette.xboxButtons
                    Rectangle {
                        width: (parent.width - 5) / 2
                        height: 32
                        radius: 5
                        color: xboxBtnMa.containsMouse ? Qt.lighter(modelData.color, 1.4) : modelData.color
                        border.color: Qt.lighter(modelData.color, 1.6)
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            color: "white"
                            font.pixelSize: 11
                            font.bold: true
                        }

                        MouseArea {
                            id: xboxBtnMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                var uid = "button_" + Date.now()
                                palette.addWidget({
                                    "id": uid,
                                    "type": "button",
                                    "x": 400,
                                    "y": 300,
                                    "width": 60,
                                    "height": 60,
                                    "label": modelData.label,
                                    "button_id": modelData.id,
                                    "color": modelData.color,
                                    "shape": "circle",
                                    "toggle_mode": false
                                })
                            }
                        }
                    }
                }
            }
        }

        // LT — Left Trigger (ViGEm only, maps to z axis)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode === "vigem"
            color: ltArea.containsMouse ? "#5a4a2a" : "#463b20"
            border.color: "#aa8a3a"
            border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 6
                Text { text: "▬"; color: "#ffcc55"; font.pixelSize: 16 }
                Text { text: "LT (Trigger)"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }
            MouseArea {
                id: ltArea; anchors.fill: parent; hoverEnabled: true
                onClicked: palette.addWidget({ "id": "slider_" + Date.now(), "type": "slider",
                    "x": 100, "y": 100, "width": 160, "height": 50, "label": "LT",
                    "orientation": "horizontal", "snap_mode": "left",
                    "mapping": {"axis": "z"} })
            }
        }

        // RT — Right Trigger (ViGEm only, maps to rz axis)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode === "vigem"
            color: rtArea.containsMouse ? "#5a4a2a" : "#463b20"
            border.color: "#aa8a3a"
            border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.margins: 6; spacing: 6
                Text { text: "▬"; color: "#ffcc55"; font.pixelSize: 16 }
                Text { text: "RT (Trigger)"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }
            MouseArea {
                id: rtArea; anchors.fill: parent; hoverEnabled: true
                onClicked: palette.addWidget({ "id": "slider_" + Date.now(), "type": "slider",
                    "x": 300, "y": 100, "width": 160, "height": 50, "label": "RT",
                    "orientation": "horizontal", "snap_mode": "left",
                    "mapping": {"axis": "rz"} })
            }
        }

        // Add Horizontal Slider (vJoy only)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode !== "vigem"
            color: sliderAddArea.containsMouse ? "#3a5a3a" : "#2e4e2e"
            border.color: "#4aaa4a"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "▬"; color: "#6aff6a"; font.pixelSize: 16 }
                Text { text: "H Slider"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: sliderAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "slider_" + Date.now()
                    var axis = palette._nextSingleAxis()
                    palette.addWidget({
                        "id": uid,
                        "type": "slider",
                        "x": 300,
                        "y": 100,
                        "width": 160,
                        "height": 50,
                        "label": "Slider",
                        "orientation": "horizontal",
                        "center_return": false,
                        "mapping": {"axis": axis}
                    })
                }
            }
        }

        // Add Vertical Slider (vJoy only)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode !== "vigem"
            color: vSliderAddArea.containsMouse ? "#3a5a3a" : "#2e4e2e"
            border.color: "#4aaa4a"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "▮"; color: "#6aff6a"; font.pixelSize: 16 }
                Text { text: "V Slider"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: vSliderAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "vslider_" + Date.now()
                    var axis = palette._nextSingleAxis()
                    palette.addWidget({
                        "id": uid,
                        "type": "slider",
                        "x": 300,
                        "y": 100,
                        "width": 50,
                        "height": 160,
                        "label": "Slider",
                        "orientation": "vertical",
                        "center_return": false,
                        "mapping": {"axis": axis}
                    })
                }
            }
        }

        // Add D-Pad
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            color: dpadAddArea.containsMouse ? "#4a4a3a" : "#3e3e2e"
            border.color: "#aaaa4a"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "+"; color: "#ffff6a"; font.pixelSize: 16; font.bold: true }
                Text { text: "D-Pad"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: dpadAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "dpad_" + Date.now()
                    var upId = palette._nextButtonId()
                    // Temporarily add up to used set for subsequent calls
                    var downId = upId + 1
                    var leftId = upId + 2
                    var rightId = upId + 3
                    var mapping = palette.outputMode === "vigem"
                        ? {"up": 11, "down": 12, "left": 13, "right": 14}
                        : {"up": upId, "down": downId, "left": leftId, "right": rightId}
                    palette.addWidget({
                        "id": uid,
                        "type": "dpad",
                        "x": 350,
                        "y": 250,
                        "width": 140,
                        "height": 140,
                        "label": "D-Pad",
                        "mapping": mapping
                    })
                }
            }
        }

        // Add Steering Wheel (vJoy only)
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            visible: palette.outputMode !== "vigem"
            color: wheelAddArea.containsMouse ? "#4a3a5a" : "#3e2e4e"
            border.color: "#aa4aaa"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6

                Text { text: "O"; color: "#cc6aff"; font.pixelSize: 16; font.bold: true }
                Text { text: "Wheel"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: wheelAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "wheel_" + Date.now()
                    var axis = palette._nextSingleAxis()
                    palette.addWidget({
                        "id": uid,
                        "type": "wheel",
                        "x": 350,
                        "y": 200,
                        "width": 150,
                        "height": 150,
                        "label": "Wheel",
                        "mapping": {"axis": axis}
                    })
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#444" }

        // Axis limits info
        Text {
            text: palette.outputMode === "vigem" ? "Xbox Limits:" : "Axis Limits:"
            color: "#aaa"
            font.pixelSize: 10
            font.bold: true
        }
        Text {
            text: palette.outputMode === "vigem"
                ? "2 sticks, 2 triggers\n10 buttons + D-Pad"
                : "4 sticks (8 axes)\n128 buttons"
            color: "#888"
            font.pixelSize: 9
            lineHeight: 1.3
        }
        Text {
            text: "Triple-click joystick\nto lock mouse to it"
            color: "#ff6a00"
            font.pixelSize: 8
            lineHeight: 1.3
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#444" }

        // Toggle Grid
        Rectangle {
            Layout.fillWidth: true
            height: 30
            radius: 4
            color: gridToggleArea.containsMouse ? "#444" : "#333"
            border.color: "#555"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "Toggle Grid"
                color: "#ccc"
                font.pixelSize: 11
            }

            MouseArea {
                id: gridToggleArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: palette.toggleGrid()
            }
        }

        // Axis exhaustion warning
        Rectangle {
            Layout.fillWidth: true
            height: axisWarnText.height + 8
            radius: 4
            color: "#442200"
            border.color: "#ff6a00"
            border.width: 1
            visible: palette._allSingleAxesUsed()

            Text {
                id: axisWarnText
                anchors.centerIn: parent
                width: parent.width - 8
                text: "All 8 axes in use"
                color: "#ff6a00"
                font.pixelSize: 9
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        // Save As
        Rectangle {
            Layout.fillWidth: true
            height: 30
            radius: 4
            color: saveAsArea.containsMouse ? "#444" : "#333"
            border.color: "#555"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "Save Layout As..."
                color: "#ccc"
                font.pixelSize: 11
            }

            MouseArea {
                id: saveAsArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: palette.saveLayoutAs("")
            }
        }

        // Done Editing
        Rectangle {
            Layout.fillWidth: true
            height: 34
            radius: 6
            color: doneArea.containsMouse ? "#1a8cff" : "#0078d4"

            Row {
                anchors.centerIn: parent
                spacing: 6
                Text { text: "\u2713"; color: "white"; font.pixelSize: 14 }
                Text { text: "Done Editing"; color: "white"; font.pixelSize: 12; font.bold: true }
            }

            MouseArea {
                id: doneArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: palette.doneEditing()
            }
        }

        Item { Layout.fillHeight: true }
    }
    }
}
