import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15

Item {
    id: root
    property real scaleFactor: 1.0
    // First button number
    property int startId: 1
    // How many buttons to render
    property int buttonCount: 4
    // Track version so bindings re-evaluate when dialog saves
    property int buttonsVersion: (typeof controller !== 'undefined' && controller) ? controller.buttonsVersion : 0

    // Base metrics
    readonly property real baseWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(160) : 160
    readonly property real baseHeight: (typeof controller !== 'undefined' && controller) ? controller.scaled(120) : 120
    readonly property real baseBtnW: (typeof controller !== 'undefined' && controller) ? controller.scaled(68) : 68
    readonly property real baseBtnH: (typeof controller !== 'undefined' && controller) ? controller.scaled(42) : 42
    readonly property real baseRowSpace: (typeof controller !== 'undefined' && controller) ? controller.scaled(12) : 12
    readonly property real baseColSpace: (typeof controller !== 'undefined' && controller) ? controller.scaled(16) : 16
    // Compute scale from width only to avoid feedback cycles with height
    readonly property real scale: Math.max(0.5, Math.min(2.0, width / baseWidth))

    // Provide sensible implicit size but do not drive layout from content to avoid cycles
    implicitWidth: baseWidth
    implicitHeight: baseHeight

    GridLayout {
        id: grid
        anchors.fill: parent
        columns: 2
        rowSpacing: root.baseRowSpace * root.scale
        columnSpacing: root.baseColSpace * root.scale

        Repeater {
            id: rep
            // Avoid binding loop with Repeater.count by referencing root.buttonCount
            model: root.buttonCount
            delegate: Basic.Button {
                readonly property int bid: startId + index
                // Make sure binding depends on controller.buttonsVersion
                readonly property int _dep: (typeof controller !== 'undefined' && controller) ? controller.buttonsVersion : 0
                text: bid.toString()
                Layout.preferredWidth: root.baseBtnW * root.scale
                Layout.preferredHeight: root.baseBtnH * root.scale
                // Toggle vs momentary behavior from config via bridge
                checkable: controller ? (root.buttonsVersion, controller.isButtonToggle(bid)) : false
                onCheckableChanged: {
                    // If switching to momentary while currently latched, clear it and release vJoy
                    if (!checkable && checked) {
                        checked = false
                        if (controller) controller.setButton(bid, false)
                    }
                }
                onToggled: if (checkable && controller) controller.setButton(bid, checked)
                onPressed: if (!checkable && controller) controller.setButton(bid, true)
                onReleased: if (!checkable && controller) controller.setButton(bid, false)

                // Blue pressed/checked style
                contentItem: Label {
                    text: parent.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: (parent.pressed || parent.checked) ? "white" : "#eaeaea"
                }
                background: Rectangle {
                    radius: (typeof controller !== 'undefined' && controller) ? controller.scaled(4) : 4
                    color: (parent.pressed || parent.checked) ? "#3264c8" : "#2a2a2a"
                    border.color: (parent.pressed || parent.checked) ? "#86a8ff" : "#444"
                    border.width: 1
                }
            }
        }
    }
}
