import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: root
    property real scaleFactor: 1.0

    // Helper for scaled values
    function scaled(v) { return controller ? controller.scaled(v) : v }

    // Controller body background
    Rectangle {
        id: controllerBody
        anchors.centerIn: parent
        width: Math.min(parent.width - scaled(20), scaled(800))
        height: Math.min(parent.height - scaled(20), scaled(500))
        color: "#1a1a1a"
        radius: scaled(40)
        border.color: "#333"
        border.width: 2

        // Left grip
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: -scaled(30)
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: scaled(40)
            width: scaled(80)
            height: scaled(200)
            color: "#1a1a1a"
            radius: scaled(35)
            border.color: "#333"
            border.width: 2
        }

        // Right grip
        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: -scaled(30)
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: scaled(40)
            width: scaled(80)
            height: scaled(200)
            color: "#1a1a1a"
            radius: scaled(35)
            border.color: "#333"
            border.width: 2
        }

        // =========== LEFT BUMPER (LB) ===========
        Rectangle {
            id: lbBumper
            anchors.left: parent.left
            anchors.leftMargin: scaled(40)
            anchors.top: parent.top
            anchors.topMargin: -scaled(8)
            width: scaled(100)
            height: scaled(35)
            radius: scaled(8)
            color: lbArea.pressed ? "#555" : "#2d2d2d"
            border.color: "#444"
            border.width: 1

            Label { anchors.centerIn: parent; text: "LB"; color: "#ccc"; font.pixelSize: scaled(14); font.bold: true }

            MouseArea {
                id: lbArea
                anchors.fill: parent
                onPressed: if (controller) controller.setButton(5, true)
                onReleased: if (controller) controller.setButton(5, false)
            }
        }

        // =========== LEFT TRIGGER (LT) ===========
        Rectangle {
            id: ltTrigger
            anchors.left: lbBumper.left
            anchors.bottom: lbBumper.top
            anchors.bottomMargin: scaled(5)
            width: scaled(70)
            height: scaled(50)
            radius: scaled(10)
            color: "#252525"
            border.color: "#444"
            border.width: 1

            Label { 
                anchors.top: parent.top
                anchors.topMargin: scaled(4)
                anchors.horizontalCenter: parent.horizontalCenter
                text: "LT"; color: "#888"; font.pixelSize: scaled(11) 
            }

            // Trigger slider
            Rectangle {
                id: ltTrack
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(6)
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(50)
                height: scaled(20)
                radius: scaled(4)
                color: "#1a1a1a"

                Rectangle {
                    id: ltFill
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * ltDragArea.value
                    radius: scaled(4)
                    color: "#107c10"
                }

                MouseArea {
                    id: ltDragArea
                    property real value: 0
                    anchors.fill: parent
                    onPositionChanged: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        if (controller) controller.setThrottle(value)
                    }
                    onPressed: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        if (controller) controller.setThrottle(value)
                    }
                    onReleased: {
                        value = 0
                        if (controller) controller.setThrottle(0)
                    }
                }
            }
        }

        // =========== RIGHT BUMPER (RB) ===========
        Rectangle {
            id: rbBumper
            anchors.right: parent.right
            anchors.rightMargin: scaled(40)
            anchors.top: parent.top
            anchors.topMargin: -scaled(8)
            width: scaled(100)
            height: scaled(35)
            radius: scaled(8)
            color: rbArea.pressed ? "#555" : "#2d2d2d"
            border.color: "#444"
            border.width: 1

            Label { anchors.centerIn: parent; text: "RB"; color: "#ccc"; font.pixelSize: scaled(14); font.bold: true }

            MouseArea {
                id: rbArea
                anchors.fill: parent
                onPressed: if (controller) controller.setButton(6, true)
                onReleased: if (controller) controller.setButton(6, false)
            }
        }

        // =========== RIGHT TRIGGER (RT) ===========
        Rectangle {
            id: rtTrigger
            anchors.right: rbBumper.right
            anchors.bottom: rbBumper.top
            anchors.bottomMargin: scaled(5)
            width: scaled(70)
            height: scaled(50)
            radius: scaled(10)
            color: "#252525"
            border.color: "#444"
            border.width: 1

            Label { 
                anchors.top: parent.top
                anchors.topMargin: scaled(4)
                anchors.horizontalCenter: parent.horizontalCenter
                text: "RT"; color: "#888"; font.pixelSize: scaled(11) 
            }

            Rectangle {
                id: rtTrack
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(6)
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(50)
                height: scaled(20)
                radius: scaled(4)
                color: "#1a1a1a"

                Rectangle {
                    id: rtFill
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * rtDragArea.value
                    radius: scaled(4)
                    color: "#107c10"
                }

                MouseArea {
                    id: rtDragArea
                    property real value: 0
                    anchors.fill: parent
                    onPositionChanged: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        if (controller) controller.setRudder(value * 2 - 1)
                    }
                    onPressed: function(mouse) {
                        value = Math.max(0, Math.min(1, mouse.x / width))
                        if (controller) controller.setRudder(value * 2 - 1)
                    }
                    onReleased: {
                        value = 0
                        if (controller) controller.setRudder(-1)
                    }
                }
            }
        }

        // =========== LEFT STICK ===========
        Item {
            id: leftStickArea
            anchors.left: parent.left
            anchors.leftMargin: scaled(60)
            anchors.top: parent.top
            anchors.topMargin: scaled(60)
            width: scaled(160)
            height: scaled(160)

            Comp.Joystick {
                anchors.centerIn: parent
                width: scaled(140)
                height: scaled(140)
                onMoved: function(x, y) { if (controller) controller.setLeftStick(x, -y) }
            }

            // LS click button
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(36)
                height: scaled(20)
                radius: scaled(4)
                color: lsArea.pressed ? "#444" : "#252525"
                border.color: "#555"
                border.width: 1

                Label { anchors.centerIn: parent; text: "LS"; color: "#aaa"; font.pixelSize: scaled(10) }

                MouseArea {
                    id: lsArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(9, true)
                    onReleased: if (controller) controller.setButton(9, false)
                }
            }
        }

        // =========== D-PAD ===========
        Item {
            id: dpadArea
            anchors.left: parent.left
            anchors.leftMargin: scaled(70)
            anchors.bottom: parent.bottom
            anchors.bottomMargin: scaled(50)
            width: scaled(130)
            height: scaled(130)

            // D-Pad background circle
            Rectangle {
                anchors.centerIn: parent
                width: scaled(120)
                height: scaled(120)
                radius: scaled(60)
                color: "#252525"
                border.color: "#3a3a3a"
                border.width: 2
            }

            // D-Pad cross
            // Up
            Rectangle {
                id: dpadUp
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: scaled(8)
                width: scaled(38)
                height: scaled(45)
                radius: scaled(6)
                color: dpadUpArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 1

                Label { anchors.centerIn: parent; text: "▲"; color: "#aaa"; font.pixelSize: scaled(16) }

                MouseArea {
                    id: dpadUpArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(11, true)
                    onReleased: if (controller) controller.setButton(11, false)
                }
            }

            // Down
            Rectangle {
                id: dpadDown
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(8)
                width: scaled(38)
                height: scaled(45)
                radius: scaled(6)
                color: dpadDownArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 1

                Label { anchors.centerIn: parent; text: "▼"; color: "#aaa"; font.pixelSize: scaled(16) }

                MouseArea {
                    id: dpadDownArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(12, true)
                    onReleased: if (controller) controller.setButton(12, false)
                }
            }

            // Left
            Rectangle {
                id: dpadLeft
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: scaled(8)
                width: scaled(45)
                height: scaled(38)
                radius: scaled(6)
                color: dpadLeftArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 1

                Label { anchors.centerIn: parent; text: "◄"; color: "#aaa"; font.pixelSize: scaled(16) }

                MouseArea {
                    id: dpadLeftArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(13, true)
                    onReleased: if (controller) controller.setButton(13, false)
                }
            }

            // Right
            Rectangle {
                id: dpadRight
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: scaled(8)
                width: scaled(45)
                height: scaled(38)
                radius: scaled(6)
                color: dpadRightArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 1

                Label { anchors.centerIn: parent; text: "►"; color: "#aaa"; font.pixelSize: scaled(16) }

                MouseArea {
                    id: dpadRightArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(14, true)
                    onReleased: if (controller) controller.setButton(14, false)
                }
            }
        }

        // =========== CENTER BUTTONS (Back, Xbox, Start) ===========
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: scaled(80)
            spacing: scaled(20)

            // View (Back) button
            Rectangle {
                width: scaled(40)
                height: scaled(40)
                radius: scaled(20)
                color: viewArea.pressed ? "#444" : "#2a2a2a"
                border.color: "#555"
                border.width: 1

                Label { anchors.centerIn: parent; text: "☰"; color: "#aaa"; font.pixelSize: scaled(14) }

                MouseArea {
                    id: viewArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(7, true)
                    onReleased: if (controller) controller.setButton(7, false)
                }
            }

            // Xbox button
            Rectangle {
                width: scaled(50)
                height: scaled(50)
                radius: scaled(25)
                color: "#107c10"
                border.color: "#1a9f1a"
                border.width: 2

                Label { anchors.centerIn: parent; text: "X"; color: "white"; font.pixelSize: scaled(22); font.bold: true }
            }

            // Menu (Start) button
            Rectangle {
                width: scaled(40)
                height: scaled(40)
                radius: scaled(20)
                color: menuArea.pressed ? "#444" : "#2a2a2a"
                border.color: "#555"
                border.width: 1

                Label { anchors.centerIn: parent; text: "≡"; color: "#aaa"; font.pixelSize: scaled(16) }

                MouseArea {
                    id: menuArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(8, true)
                    onReleased: if (controller) controller.setButton(8, false)
                }
            }
        }

        // =========== FACE BUTTONS (A, B, X, Y) ===========
        Item {
            id: faceButtonsArea
            anchors.right: parent.right
            anchors.rightMargin: scaled(60)
            anchors.top: parent.top
            anchors.topMargin: scaled(60)
            width: scaled(140)
            height: scaled(140)

            // Y - Yellow (top)
            Rectangle {
                id: btnY
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                width: scaled(48)
                height: scaled(48)
                radius: scaled(24)
                color: yArea.pressed ? "#e6b800" : "#d4a017"
                border.color: "#ffd700"
                border.width: 3

                Label { anchors.centerIn: parent; text: "Y"; color: "white"; font.pixelSize: scaled(20); font.bold: true }

                MouseArea {
                    id: yArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(4, true)
                    onReleased: if (controller) controller.setButton(4, false)
                }
            }

            // X - Blue (left)
            Rectangle {
                id: btnX
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                width: scaled(48)
                height: scaled(48)
                radius: scaled(24)
                color: xArea.pressed ? "#3b82f6" : "#2563eb"
                border.color: "#60a5fa"
                border.width: 3

                Label { anchors.centerIn: parent; text: "X"; color: "white"; font.pixelSize: scaled(20); font.bold: true }

                MouseArea {
                    id: xArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(3, true)
                    onReleased: if (controller) controller.setButton(3, false)
                }
            }

            // B - Red (right)
            Rectangle {
                id: btnB
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                width: scaled(48)
                height: scaled(48)
                radius: scaled(24)
                color: bArea.pressed ? "#ef4444" : "#dc2626"
                border.color: "#f87171"
                border.width: 3

                Label { anchors.centerIn: parent; text: "B"; color: "white"; font.pixelSize: scaled(20); font.bold: true }

                MouseArea {
                    id: bArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(2, true)
                    onReleased: if (controller) controller.setButton(2, false)
                }
            }

            // A - Green (bottom)
            Rectangle {
                id: btnA
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                width: scaled(48)
                height: scaled(48)
                radius: scaled(24)
                color: aArea.pressed ? "#22c55e" : "#16a34a"
                border.color: "#4ade80"
                border.width: 3

                Label { anchors.centerIn: parent; text: "A"; color: "white"; font.pixelSize: scaled(20); font.bold: true }

                MouseArea {
                    id: aArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(1, true)
                    onReleased: if (controller) controller.setButton(1, false)
                }
            }
        }

        // =========== RIGHT STICK ===========
        Item {
            id: rightStickArea
            anchors.right: parent.right
            anchors.rightMargin: scaled(150)
            anchors.bottom: parent.bottom
            anchors.bottomMargin: scaled(50)
            width: scaled(160)
            height: scaled(160)

            Comp.Joystick {
                anchors.centerIn: parent
                width: scaled(130)
                height: scaled(130)
                onMoved: function(x, y) { if (controller) controller.setRightStick(x, -y) }
            }

            // RS click button
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(36)
                height: scaled(20)
                radius: scaled(4)
                color: rsArea.pressed ? "#444" : "#252525"
                border.color: "#555"
                border.width: 1

                Label { anchors.centerIn: parent; text: "RS"; color: "#aaa"; font.pixelSize: scaled(10) }

                MouseArea {
                    id: rsArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(10, true)
                    onReleased: if (controller) controller.setButton(10, false)
                }
            }
        }
    }
}
