import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: palette
    color: "#2a2a2a"
    border.color: "#444"
    border.width: 1
    radius: 8
    visible: editMode

    property bool editMode: false
    property int gridSnap: 10

    // Signals to parent
    signal addWidget(var widgetData)
    signal saveLayout()
    signal toggleGrid()

    // Track available axes for joystick assignment
    readonly property var availableAxes: [
        {pair: "x/y", label: "Left Stick (X/Y)"},
        {pair: "rx/ry", label: "Right Stick (RX/RY)"},
        {pair: "z/rz", label: "Throttle/Rudder (Z/RZ)"}
    ]

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
                    palette.addWidget({
                        "id": uid,
                        "type": "joystick",
                        "x": 100,
                        "y": 200,
                        "width": 180,
                        "height": 180,
                        "label": "Stick",
                        "mapping": {"axis_x": "x", "axis_y": "y"}
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
                    var uid = "button_" + Date.now()
                    palette.addWidget({
                        "id": uid,
                        "type": "button",
                        "x": 400,
                        "y": 300,
                        "width": 60,
                        "height": 60,
                        "label": "Btn",
                        "button_id": 1,
                        "color": "#333333",
                        "shape": "circle"
                    })
                }
            }
        }

        // Add Slider
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
                Text { text: "Slider"; color: "#ddd"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
            }

            MouseArea {
                id: sliderAddArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    var uid = "slider_" + Date.now()
                    palette.addWidget({
                        "id": uid,
                        "type": "slider",
                        "x": 300,
                        "y": 100,
                        "width": 160,
                        "height": 50,
                        "label": "Slider",
                        "orientation": "horizontal",
                        "mapping": {"axis": "z"}
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
            text: "• vJoy: 3 sticks max\n• ViGEm: 2 sticks max\n• Buttons: up to 128"
            color: "#888"
            font.pixelSize: 9
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

        // Save Layout
        Rectangle {
            Layout.fillWidth: true
            height: 34
            radius: 6
            color: saveArea.containsMouse ? "#1a8cff" : "#0078d4"

            Text {
                anchors.centerIn: parent
                text: "Save Layout"
                color: "white"
                font.pixelSize: 12
                font.bold: true
            }

            MouseArea {
                id: saveArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: palette.saveLayout()
            }
        }

        Item { Layout.fillHeight: true }
    }
}
