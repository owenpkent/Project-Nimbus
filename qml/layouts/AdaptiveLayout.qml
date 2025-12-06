import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: root
    property real scaleFactor: 1.0

    // Minimum size constants to prevent overlap
    readonly property real minWidth: 700
    readonly property real minHeight: 450

    // Calculate effective scale factor with minimum to prevent squishing
    // Use higher minimum (0.95) to prevent overlap at small window sizes
    readonly property real effectiveScale: Math.max(0.95, controller ? controller.scaleFactor : 1.0)

    // Helper for scaled values - uses effectiveScale with minimum
    function scaled(v) { return v * effectiveScale }

    // Accessibility-focused sizes - balanced for small window support
    readonly property real joystickSize: scaled(140)      // Smaller for better fit
    readonly property real dpadSize: scaled(110)          // Smaller D-pad to prevent overlap
    readonly property real faceButtonSize: scaled(52)     // Smaller ABXY buttons
    readonly property real triggerWidth: scaled(75)       // Narrower triggers
    readonly property real triggerHeight: scaled(48)      // Shorter triggers
    readonly property real bumperWidth: scaled(100)       // Narrower bumpers

    // Controller body background
    Rectangle {
        id: controllerBody
        anchors.centerIn: parent
        // Ensure minimum margins from window edges - always visible border
        width: Math.min(parent.width - 20, Math.max(minWidth, scaled(900)))
        height: Math.min(parent.height - 20, Math.max(minHeight, scaled(550)))
        color: "#1a1a1a"
        radius: scaled(30)
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

        // =========== LEFT TRIGGER (LT) - Inside controller body ===========
        Rectangle {
            id: ltTrigger
            anchors.left: parent.left
            anchors.leftMargin: scaled(25)
            anchors.top: parent.top
            anchors.topMargin: scaled(12)
            width: triggerWidth
            height: triggerHeight
            radius: scaled(10)
            color: "#252525"
            border.color: "#444"
            border.width: 2

            Label { 
                anchors.top: parent.top
                anchors.topMargin: scaled(4)
                anchors.horizontalCenter: parent.horizontalCenter
                text: "LT"; color: "#aaa"; font.pixelSize: scaled(12); font.bold: true
            }

            // Trigger slider - larger for accessibility
            Rectangle {
                id: ltTrack
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(8)
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - scaled(16)
                height: scaled(24)
                radius: scaled(6)
                color: "#1a1a1a"

                Rectangle {
                    id: ltFill
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * ltDragArea.value
                    radius: scaled(6)
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

        // =========== LEFT BUMPER (LB) ===========
        Rectangle {
            id: lbBumper
            anchors.left: ltTrigger.right
            anchors.leftMargin: scaled(10)
            anchors.verticalCenter: ltTrigger.verticalCenter
            width: bumperWidth
            height: scaled(45)
            radius: scaled(10)
            color: lbArea.pressed ? "#555" : "#2d2d2d"
            border.color: "#444"
            border.width: 2

            Label { anchors.centerIn: parent; text: "LB"; color: "#ccc"; font.pixelSize: scaled(18); font.bold: true }

            MouseArea {
                id: lbArea
                anchors.fill: parent
                onPressed: if (controller) controller.setButton(5, true)
                onReleased: if (controller) controller.setButton(5, false)
            }
        }

        // =========== RIGHT TRIGGER (RT) - Inside controller body ===========
        Rectangle {
            id: rtTrigger
            anchors.right: parent.right
            anchors.rightMargin: scaled(25)
            anchors.top: parent.top
            anchors.topMargin: scaled(12)
            width: triggerWidth
            height: triggerHeight
            radius: scaled(10)
            color: "#252525"
            border.color: "#444"
            border.width: 2

            Label { 
                anchors.top: parent.top
                anchors.topMargin: scaled(4)
                anchors.horizontalCenter: parent.horizontalCenter
                text: "RT"; color: "#aaa"; font.pixelSize: scaled(12); font.bold: true
            }

            Rectangle {
                id: rtTrack
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(8)
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - scaled(16)
                height: scaled(24)
                radius: scaled(6)
                color: "#1a1a1a"

                Rectangle {
                    id: rtFill
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * rtDragArea.value
                    radius: scaled(6)
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

        // =========== RIGHT BUMPER (RB) ===========
        Rectangle {
            id: rbBumper
            anchors.right: rtTrigger.left
            anchors.rightMargin: scaled(10)
            anchors.verticalCenter: rtTrigger.verticalCenter
            width: bumperWidth
            height: scaled(45)
            radius: scaled(10)
            color: rbArea.pressed ? "#555" : "#2d2d2d"
            border.color: "#444"
            border.width: 2

            Label { anchors.centerIn: parent; text: "RB"; color: "#ccc"; font.pixelSize: scaled(18); font.bold: true }

            MouseArea {
                id: rbArea
                anchors.fill: parent
                onPressed: if (controller) controller.setButton(6, true)
                onReleased: if (controller) controller.setButton(6, false)
            }
        }

        // =========== LEFT STICK ===========
        Item {
            id: leftStickArea
            anchors.left: parent.left
            anchors.leftMargin: scaled(45)
            anchors.top: ltTrigger.bottom
            anchors.topMargin: scaled(20)
            width: joystickSize + scaled(15)
            height: joystickSize + scaled(30)

            Comp.Joystick {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -scaled(8)
                width: joystickSize
                height: joystickSize
                onMoved: function(x, y) { if (controller) controller.setLeftStick(x, -y) }
            }

            // LS click button (L3) - positioned below joystick
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(70)
                height: scaled(40)
                radius: scaled(8)
                color: lsArea.pressed ? "#4a4a4a" : "#2d2d2d"
                border.color: lsArea.pressed ? "#6aa3ff" : "#555"
                border.width: 2

                Label { 
                    anchors.centerIn: parent
                    text: "L3"
                    color: lsArea.pressed ? "#fff" : "#ccc"
                    font.pixelSize: scaled(16)
                    font.bold: true
                }

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
            anchors.leftMargin: scaled(50)
            anchors.bottom: parent.bottom
            anchors.bottomMargin: scaled(25)
            width: dpadSize
            height: dpadSize

            // D-Pad background circle
            Rectangle {
                anchors.centerIn: parent
                width: dpadSize
                height: dpadSize
                radius: dpadSize / 2
                color: "#252525"
                border.color: "#3a3a3a"
                border.width: 2
            }

            // D-Pad Up
            Rectangle {
                id: dpadUp
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: scaled(6)
                width: scaled(40)
                height: scaled(42)
                radius: scaled(6)
                color: dpadUpArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 2

                Label { anchors.centerIn: parent; text: "▲"; color: "#aaa"; font.pixelSize: scaled(18) }

                MouseArea {
                    id: dpadUpArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(11, true)
                    onReleased: if (controller) controller.setButton(11, false)
                }
            }

            // D-Pad Down
            Rectangle {
                id: dpadDown
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: scaled(6)
                width: scaled(40)
                height: scaled(42)
                radius: scaled(6)
                color: dpadDownArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 2

                Label { anchors.centerIn: parent; text: "▼"; color: "#aaa"; font.pixelSize: scaled(18) }

                MouseArea {
                    id: dpadDownArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(12, true)
                    onReleased: if (controller) controller.setButton(12, false)
                }
            }

            // D-Pad Left
            Rectangle {
                id: dpadLeft
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: scaled(6)
                width: scaled(42)
                height: scaled(40)
                radius: scaled(6)
                color: dpadLeftArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 2

                Label { anchors.centerIn: parent; text: "◄"; color: "#aaa"; font.pixelSize: scaled(18) }

                MouseArea {
                    id: dpadLeftArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(13, true)
                    onReleased: if (controller) controller.setButton(13, false)
                }
            }

            // D-Pad Right
            Rectangle {
                id: dpadRight
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: scaled(6)
                width: scaled(42)
                height: scaled(40)
                radius: scaled(6)
                color: dpadRightArea.pressed ? "#555" : "#333"
                border.color: "#444"
                border.width: 2

                Label { anchors.centerIn: parent; text: "►"; color: "#aaa"; font.pixelSize: scaled(18) }

                MouseArea {
                    id: dpadRightArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(14, true)
                    onReleased: if (controller) controller.setButton(14, false)
                }
            }
        }

        // =========== CENTER BUTTONS (Back, Guide, Start) - All matching gray with Greek symbols ===========
        Row {
            id: centerButtons
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: scaled(90)
            spacing: scaled(20)

            // View (Back) button - Alpha
            Rectangle {
                width: scaled(50)
                height: scaled(50)
                radius: scaled(25)
                color: viewArea.pressed ? "#4a4a4a" : "#333"
                border.color: viewArea.pressed ? "#888" : "#555"
                border.width: 2

                Label { 
                    anchors.centerIn: parent
                    text: "α"
                    color: viewArea.pressed ? "#fff" : "#aaa"
                    font.pixelSize: scaled(22)
                }

                MouseArea {
                    id: viewArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(7, true)
                    onReleased: if (controller) controller.setButton(7, false)
                }
            }

            // Guide/Home button - Omega (center)
            Rectangle {
                width: scaled(50)
                height: scaled(50)
                radius: scaled(25)
                color: guideArea.pressed ? "#4a4a4a" : "#333"
                border.color: guideArea.pressed ? "#888" : "#555"
                border.width: 2

                Label { 
                    anchors.centerIn: parent
                    text: "Ω"
                    color: guideArea.pressed ? "#fff" : "#aaa"
                    font.pixelSize: scaled(22)
                }

                MouseArea {
                    id: guideArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(15, true)
                    onReleased: if (controller) controller.setButton(15, false)
                }
            }

            // Menu (Start) button - Beta
            Rectangle {
                width: scaled(50)
                height: scaled(50)
                radius: scaled(25)
                color: menuArea.pressed ? "#4a4a4a" : "#333"
                border.color: menuArea.pressed ? "#888" : "#555"
                border.width: 2

                Label { 
                    anchors.centerIn: parent
                    text: "β"
                    color: menuArea.pressed ? "#fff" : "#aaa"
                    font.pixelSize: scaled(22)
                }

                MouseArea {
                    id: menuArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(8, true)
                    onReleased: if (controller) controller.setButton(8, false)
                }
            }
        }

        // =========== FACE BUTTONS (A, B, X, Y) - Larger for accessibility ===========
        Item {
            id: faceButtonsArea
            anchors.right: parent.right
            anchors.rightMargin: scaled(50)
            anchors.top: rtTrigger.bottom
            anchors.topMargin: scaled(30)
            width: faceButtonSize * 3
            height: faceButtonSize * 3

            // Y - Yellow (top)
            Rectangle {
                id: btnY
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                width: faceButtonSize
                height: faceButtonSize
                radius: faceButtonSize / 2
                color: yArea.pressed ? "#e6b800" : "#d4a017"
                border.color: "#ffd700"
                border.width: 4

                Label { anchors.centerIn: parent; text: "Y"; color: "white"; font.pixelSize: scaled(28); font.bold: true }

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
                width: faceButtonSize
                height: faceButtonSize
                radius: faceButtonSize / 2
                color: xArea.pressed ? "#3b82f6" : "#2563eb"
                border.color: "#60a5fa"
                border.width: 4

                Label { anchors.centerIn: parent; text: "X"; color: "white"; font.pixelSize: scaled(28); font.bold: true }

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
                width: faceButtonSize
                height: faceButtonSize
                radius: faceButtonSize / 2
                color: bArea.pressed ? "#ef4444" : "#dc2626"
                border.color: "#f87171"
                border.width: 4

                Label { anchors.centerIn: parent; text: "B"; color: "white"; font.pixelSize: scaled(28); font.bold: true }

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
                width: faceButtonSize
                height: faceButtonSize
                radius: faceButtonSize / 2
                color: aArea.pressed ? "#22c55e" : "#16a34a"
                border.color: "#4ade80"
                border.width: 4

                Label { anchors.centerIn: parent; text: "A"; color: "white"; font.pixelSize: scaled(28); font.bold: true }

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
            anchors.rightMargin: scaled(120)
            anchors.bottom: parent.bottom
            anchors.bottomMargin: scaled(25)
            width: joystickSize + scaled(15)
            height: joystickSize + scaled(30)

            Comp.Joystick {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -scaled(8)
                width: joystickSize
                height: joystickSize
                onMoved: function(x, y) { if (controller) controller.setRightStick(x, -y) }
            }

            // RS click button (R3) - positioned below joystick
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: scaled(70)
                height: scaled(40)
                radius: scaled(8)
                color: rsArea.pressed ? "#4a4a4a" : "#2d2d2d"
                border.color: rsArea.pressed ? "#6aa3ff" : "#555"
                border.width: 2

                Label { 
                    anchors.centerIn: parent
                    text: "R3"
                    color: rsArea.pressed ? "#fff" : "#ccc"
                    font.pixelSize: scaled(16)
                    font.bold: true
                }

                MouseArea {
                    id: rsArea
                    anchors.fill: parent
                    onPressed: if (controller) controller.setButton(10, true)
                    onReleased: if (controller) controller.setButton(10, false)
                }
            }
        }

        // =========== MODE INDICATOR (for accessibility mode switching) ===========
        Rectangle {
            id: modeIndicator
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: centerButtons.bottom
            anchors.topMargin: scaled(15)
            width: scaled(200)
            height: scaled(30)
            radius: scaled(6)
            color: "#1a1a1a"
            border.color: "#333"
            border.width: 1

            Label {
                anchors.centerIn: parent
                text: "Mode: Standard"
                color: "#888"
                font.pixelSize: scaled(12)
            }
        }
    }
}
