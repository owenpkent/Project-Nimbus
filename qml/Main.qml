import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "components" as Comp

ApplicationWindow {
    id: root
    visible: true
    width: 1024
    height: 600
    minimumWidth: 256
    minimumHeight: 150
    title: "Project Nimbus - QML UI"
    background: Rectangle { color: "black" }

    // Scale factor bound to Python bridge; default 1.0
    property real scaleFactor: controller ? controller.scaleFactor : 1.0

    menuBar: MenuBar {
        Menu {
            title: qsTr("File")
            MenuItem { text: qsTr("Configure Axes"); onTriggered: controller && controller.openAxisMapping() }
            MenuItem { text: qsTr("Joystick Settings..."); onTriggered: controller && controller.openJoystickSettings() }
            MenuItem { text: qsTr("Button Settings..."); onTriggered: controller && controller.openButtonSettings() }
            MenuItem { text: qsTr("Rudder Settings..."); onTriggered: controller && controller.openRudderSettings() }
            MenuSeparator {}
            MenuItem { text: qsTr("Exit"); onTriggered: Qt.quit() }
        }
        Menu {
            title: qsTr("View")
            Menu {
                title: qsTr("Size")
                Repeater {
                    model: [0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0]
                    delegate: MenuItem {
                        readonly property real factor: modelData
                        checkable: true
                        checked: Math.abs(root.scaleFactor - factor) < 1e-6
                        text: Math.round(factor * 100) + "%"
                        onTriggered: controller && controller.setScaleFactor(factor)
                    }
                }
            }
            MenuSeparator {}
            MenuItem {
                id: debugBordersItem
                text: qsTr("Debug Borders")
                checkable: true
                checked: controller ? controller.debugBorders : false
                onTriggered: if (controller) controller.debugBorders = checked
            }
        }
    }

    RowLayout {
        id: mainRow
        anchors.fill: parent
        anchors.margins: controller ? controller.scaled(6) : 6
        spacing: controller ? controller.scaled(8) : 8

        // Left panel: joystick + number buttons (1-4)
        ColumnLayout {
            Layout.fillHeight: true
            Layout.preferredWidth: controller ? controller.scaled(280) : 280
            spacing: controller ? controller.scaled(8) : 8

            Rectangle {
                id: leftWrap
                color: "transparent"
                border.color: "#d24"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                Comp.Joystick {
                    id: leftJoy
                    anchors.centerIn: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    // Force square size so base border stays a circle
                    width: Math.min(parent.width, parent.height)
                    height: width
                    onMoved: function(x, y) { if (controller) controller.setLeftStick(x, y) }
                }
            }

            Rectangle {
                id: leftPadWrap
                color: "transparent"
                border.color: "#d24"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.alignment: Qt.AlignHCenter
                // Use stable, scaled constants to avoid layout feedback
                Layout.preferredWidth: controller ? controller.scaled(200) : 200
                Layout.preferredHeight: controller ? controller.scaled(140) : 140
                Comp.NumberPad {
                    id: leftPad
                    anchors.fill: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    scaleFactor: root.scaleFactor
                    startId: 1
                    buttonCount: 4
                }
            }
        }

        // Center column (Throttle + Rudder + ARM/RTH)
        ColumnLayout {
            Layout.fillHeight: true
            // Allow center column to grow/shrink with window width
            Layout.fillWidth: true
            Layout.preferredWidth: controller ? controller.scaled(200) : 200
            spacing: controller ? controller.scaled(8) : 8

            Rectangle {
                id: throttleWrap
                Layout.alignment: Qt.AlignHCenter
                // Allow this item to take vertical space in the column
                Layout.fillHeight: true
                // Let layout allocate remaining height; set only minimum to ensure visibility
                Layout.minimumHeight: controller ? controller.scaled(200) : 200
                // Keep throttle width constant (no horizontal resizing)
                Layout.preferredWidth: throttle.implicitWidth
                color: "transparent"
                border.color: "#ec0"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Comp.SliderVertical {
                    id: throttle
                    anchors.fill: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    scaleFactor: root.scaleFactor
                    value: 0.5
                    onValueChanged: if (controller) controller.setThrottle(value)
                }
            }

            Rectangle {
                id: rudderWrap
                Layout.fillWidth: true
                // Respect rudder's implicit height (now taller)
                Layout.preferredHeight: rudder.implicitHeight
                color: "transparent"
                border.color: "#ec0"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Comp.SliderHorizontal {
                    id: rudder
                    anchors.fill: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    scaleFactor: root.scaleFactor
                    value: 0
                    onValueChanged: if (controller) controller.setRudder(value)
                }
            }

            RowLayout {
                id: actionRow
                Layout.fillWidth: true
                spacing: controller ? controller.scaled(12) : 12
                Basic.Button {
                    text: qsTr("ARM")
                    Layout.fillWidth: true
                    Layout.preferredWidth: controller ? controller.scaled(80) : 80
                    onPressed: if (controller) controller.setButton(9, true)
                    onReleased: if (controller) controller.setButton(9, false)
                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: (parent.pressed || parent.checked) ? "white" : "#eaeaea"
                    }
                    background: Item {
                        anchors.fill: parent
                        // Simple faux shadow without external effects module
                        Rectangle { anchors.fill: parent; y: controller ? controller.scaled(3) : 3; radius: controller ? controller.scaled(4) : 4; color: "#33000000"; border.width: 0; }
                        Rectangle { id: armBg; anchors.fill: parent; radius: controller ? controller.scaled(4) : 4; color: (parent.pressed || parent.checked) ? "#3264c8" : "#2a2a2a"; border.color: (parent.pressed || parent.checked) ? "#86a8ff" : "#444"; border.width: 1 }
                    }
                }
                Basic.Button {
                    text: qsTr("RTH")
                    Layout.fillWidth: true
                    Layout.preferredWidth: controller ? controller.scaled(80) : 80
                    onPressed: if (controller) controller.setButton(10, true)
                    onReleased: if (controller) controller.setButton(10, false)
                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: (parent.pressed || parent.checked) ? "white" : "#eaeaea"
                    }
                    background: Item {
                        anchors.fill: parent
                        Rectangle { anchors.fill: parent; y: controller ? controller.scaled(3) : 3; radius: controller ? controller.scaled(4) : 4; color: "#33000000"; border.width: 0 }
                        Rectangle { id: rthBg; anchors.fill: parent; radius: controller ? controller.scaled(4) : 4; color: (parent.pressed || parent.checked) ? "#3264c8" : "#2a2a2a"; border.color: (parent.pressed || parent.checked) ? "#86a8ff" : "#444"; border.width: 1 }
                    }
                }
            }
        }

        // Right panel: joystick + number buttons (5-8)
        ColumnLayout {
            Layout.fillHeight: true
            Layout.preferredWidth: controller ? controller.scaled(280) : 280
            spacing: controller ? controller.scaled(8) : 8

            Rectangle {
                id: rightWrap
                color: "transparent"
                border.color: "#48c"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                Comp.Joystick {
                    anchors.centerIn: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    width: Math.min(parent.width, parent.height)
                    height: width
                    onMoved: function(x, y) { if (controller) controller.setRightStick(x, y) }
                }
            }

            Rectangle {
                id: rightPadWrap
                color: "transparent"
                border.color: "#48c"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.alignment: Qt.AlignHCenter
                // Use stable, scaled constants to avoid layout feedback
                Layout.preferredWidth: controller ? controller.scaled(200) : 200
                Layout.preferredHeight: controller ? controller.scaled(140) : 140
                Comp.NumberPad {
                    id: rightPad
                    anchors.fill: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    scaleFactor: root.scaleFactor
                    startId: 5
                    buttonCount: 4
                }
            }
        }
    }
}
