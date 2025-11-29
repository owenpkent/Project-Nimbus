import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: root
    property real scaleFactor: 1.0
    
    // Dynamic sizing based on window height - buttons shrink proportionally
    readonly property real buttonAreaRatio: 0.22  // Buttons take max 22% of height
    readonly property real maxButtonHeight: Math.min(height * buttonAreaRatio, controller ? controller.scaled(140) : 140)

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
                    width: Math.min(parent.width, parent.height)
                    height: width
                    onMoved: function(x, y) { if (controller) controller.setLeftStick(x, -y) }
                }
            }

            Rectangle {
                id: leftPadWrap
                color: "transparent"
                border.color: "#d24"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: root.maxButtonHeight * 1.43  // Maintain aspect ratio
                Layout.preferredHeight: root.maxButtonHeight
                Layout.maximumHeight: root.maxButtonHeight
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
            Layout.fillWidth: true
            Layout.preferredWidth: controller ? controller.scaled(200) : 200
            spacing: controller ? controller.scaled(8) : 8

            Rectangle {
                id: throttleWrap
                Layout.alignment: Qt.AlignHCenter
                Layout.fillHeight: true
                Layout.minimumHeight: controller ? controller.scaled(200) : 200
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
                Layout.preferredHeight: controller ? controller.scaled(60) : 60
                color: "transparent"
                border.color: "#ec0"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Comp.SliderHorizontal {
                    id: rudder
                    anchors.fill: parent
                    anchors.margins: (controller && controller.debugBorders) ? controller.scaled(2) : 0
                    scaleFactor: root.scaleFactor
                    value: 0
                    lockCenter: rudderLockBtn.checked
                    onValueChanged: if (controller) controller.setRudder(value)
                }
            }
            
            // Rudder Lock button
            Basic.Button {
                id: rudderLockBtn
                text: checked ? "🔒 Rudder Locked" : "🔓 Rudder Lock"
                Layout.fillWidth: true
                Layout.preferredHeight: root.maxButtonHeight * 0.28
                Layout.maximumHeight: controller ? controller.scaled(36) : 36
                checkable: true
                checked: false
                onCheckedChanged: {
                    // If unlocking, return rudder to center
                    if (!checked && rudder.value !== 0) {
                        rudder.value = 0
                        if (controller) controller.setRudder(0)
                    }
                }
                contentItem: Label {
                    text: parent.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: controller ? controller.scaled(11) : 11
                    color: parent.checked ? "white" : "#ccc"
                }
                background: Rectangle {
                    radius: controller ? controller.scaled(4) : 4
                    color: parent.checked ? "#c44" : "#2a2a2a"
                    border.color: parent.checked ? "#f66" : "#444"
                    border.width: 1
                }
            }

            RowLayout {
                id: actionRow
                Layout.fillWidth: true
                Layout.preferredHeight: root.maxButtonHeight * 0.35  // Scale with buttons
                Layout.maximumHeight: controller ? controller.scaled(50) : 50
                spacing: controller ? controller.scaled(12) : 12
                Basic.Button {
                    text: controller ? (controller.buttonsVersion, controller.getButtonLabel(9)) : "9"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    checkable: controller ? (controller.buttonsVersion, controller.isButtonToggle(9)) : false
                    onCheckableChanged: {
                        if (!checkable && checked) {
                            checked = false
                            if (controller) controller.setButton(9, false)
                        }
                    }
                    onToggled: if (checkable && controller) controller.setButton(9, checked)
                    onPressed: if (!checkable && controller) controller.setButton(9, true)
                    onReleased: if (!checkable && controller) controller.setButton(9, false)
                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: (parent.pressed || parent.checked) ? "white" : "#eaeaea"
                    }
                    background: Item {
                        anchors.fill: parent
                        Rectangle { anchors.fill: parent; y: controller ? controller.scaled(3) : 3; radius: controller ? controller.scaled(4) : 4; color: "#33000000"; border.width: 0; }
                        Rectangle { anchors.fill: parent; radius: controller ? controller.scaled(4) : 4; color: (parent.pressed || parent.checked) ? "#3264c8" : "#2a2a2a"; border.color: (parent.pressed || parent.checked) ? "#86a8ff" : "#444"; border.width: 1 }
                    }
                }
                Basic.Button {
                    text: controller ? (controller.buttonsVersion, controller.getButtonLabel(10)) : "10"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    checkable: controller ? (controller.buttonsVersion, controller.isButtonToggle(10)) : false
                    onCheckableChanged: {
                        if (!checkable && checked) {
                            checked = false
                            if (controller) controller.setButton(10, false)
                        }
                    }
                    onToggled: if (checkable && controller) controller.setButton(10, checked)
                    onPressed: if (!checkable && controller) controller.setButton(10, true)
                    onReleased: if (!checkable && controller) controller.setButton(10, false)
                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: (parent.pressed || parent.checked) ? "white" : "#eaeaea"
                    }
                    background: Item {
                        anchors.fill: parent
                        Rectangle { anchors.fill: parent; y: controller ? controller.scaled(3) : 3; radius: controller ? controller.scaled(4) : 4; color: "#33000000"; border.width: 0 }
                        Rectangle { anchors.fill: parent; radius: controller ? controller.scaled(4) : 4; color: (parent.pressed || parent.checked) ? "#3264c8" : "#2a2a2a"; border.color: (parent.pressed || parent.checked) ? "#86a8ff" : "#444"; border.width: 1 }
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
                    onMoved: function(x, y) { if (controller) controller.setRightStick(x, -y) }
                }
            }

            Rectangle {
                id: rightPadWrap
                color: "transparent"
                border.color: "#48c"; border.width: (controller && controller.debugBorders) ? 1 : 0
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: root.maxButtonHeight * 1.43  // Maintain aspect ratio
                Layout.preferredHeight: root.maxButtonHeight
                Layout.maximumHeight: root.maxButtonHeight
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
