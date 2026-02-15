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

    // Signals to parent
    signal addWidget(var widgetData)
    signal saveLayout()
    signal toggleGrid()
    signal doneEditing()
    signal saveLayoutAs(string layoutName)

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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        // Title
        Text {
            text: "🛠 Widget Palette"
            color: "#fff"
            font.pixelSize: 13
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#444" }

        // Add Joystick
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
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

        // Add Button
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
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

        // Add Horizontal Slider
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
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

        // Add Vertical Slider
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
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
                    palette.addWidget({
                        "id": uid,
                        "type": "dpad",
                        "x": 350,
                        "y": 250,
                        "width": 140,
                        "height": 140,
                        "label": "D-Pad",
                        "mapping": {"up": upId, "down": downId, "left": leftId, "right": rightId}
                    })
                }
            }
        }

        // Add Steering Wheel
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
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
            text: "Axis Limits:"
            color: "#aaa"
            font.pixelSize: 10
            font.bold: true
        }
        Text {
            text: "vJoy: 4 sticks (8 axes)\nViGEm: 2 sticks max\nButtons: up to 128"
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
