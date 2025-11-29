import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property real scaleFactor: 1.0
    // -1..1 output (left=-1, right=1)
    property real value: 0
    // When true, slider does not return to center on release
    property bool lockCenter: false

    implicitWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(200) : 200
    // Twice as tall
    implicitHeight: (typeof controller !== 'undefined' && controller) ? controller.scaled(88) : 88

    // Drag state to prevent jump-to-click
    property real _pressX: 0
    property real _startValue: 0

    Rectangle {
        id: track
        anchors.centerIn: parent
        width: parent.width
        height: (typeof controller !== 'undefined' && controller) ? controller.scaled(24) : 24
        radius: height / 2
        color: "#1e1e1e"
        border.color: "#3d3d3d"
    }

    // Removed blue fill for a cleaner, snappier rudder bar

    Rectangle {
        id: knob
        width: track.height * 1.6
        height: width
        radius: width/2
        color: "#2e6bd1"
        border.color: "#6aa3ff"
        anchors.verticalCenter: track.verticalCenter
        x: track.x + ((root.value + 1.0) / 2.0) * (track.width - width)

        // Smooth return-to-center animation for rudder (no inertia)
        Behavior on x { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
    }

    MouseArea {
        anchors.fill: track
        onPressed: function(mouse) {
            root._pressX = mouse.x
            root._startValue = root.value
        }
        onPositionChanged: function(mouse) {
            if (!pressed) return
            var dx = mouse.x - root._pressX
            var effective = Math.max(1, track.width - knob.width)
            var dv = (dx / effective) * 2.0
            var v = root._startValue + dv
            root.value = Math.max(-1, Math.min(1, v))
        }
        onReleased: {
            // Smooth return to center when released (unless locked)
            if (!root.lockCenter) {
                root.value = 0
            }
        }
    }
}
