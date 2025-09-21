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

    implicitWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(160) : 160
    implicitHeight: (typeof controller !== 'undefined' && controller) ? controller.scaled(120) : 120

    GridLayout {
        id: grid
        anchors.centerIn: parent
        columns: 2
        rowSpacing: (typeof controller !== 'undefined' && controller) ? controller.scaled(12) : 12
        columnSpacing: (typeof controller !== 'undefined' && controller) ? controller.scaled(16) : 16

        Repeater {
            id: rep
            // Avoid binding loop with Repeater.count by referencing root.buttonCount
            model: root.buttonCount
            delegate: Basic.Button {
                readonly property int bid: startId + index
                text: bid.toString()
                Layout.preferredWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(68) : 68
                Layout.preferredHeight: (typeof controller !== 'undefined' && controller) ? controller.scaled(42) : 42
                // Toggle vs momentary behavior from config via bridge
                checkable: controller ? controller.isButtonToggle(bid) : false
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
