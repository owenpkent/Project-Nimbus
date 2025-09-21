import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property real scaleFactor: 1.0
    // 0..1 output (bottom=0, top=1)
    property real value: 0.5

    // Twice as wide
    implicitWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(120) : 120
    implicitHeight: 280 * scaleFactor

    // Drag state to prevent jump-to-click
    property real _pressY: 0
    property real _startValue: 0.5

    Rectangle {
        id: track
        anchors.centerIn: parent
        // Track width scales with overall control width (responsive)
        width: Math.max(((typeof controller !== 'undefined' && controller) ? controller.scaled(16) : 16),
                        parent.width * 0.22)
        height: parent.height
        radius: width / 2
        color: "#1e1e1e"
        border.color: "#3d3d3d"
    }

    // Blue fill rising from bottom proportional to value
    Rectangle {
        id: fill
        anchors.horizontalCenter: track.horizontalCenter
        width: track.width
        radius: track.radius
        color: "#3264c8"
        opacity: 0.85
        y: track.y + (track.height - height)
        height: root.value * (track.height)
        Behavior on height { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    }

    Rectangle {
        id: knob
        width: track.width * 1.6
        height: width
        radius: width/2
        color: "#2e6bd1"
        border.color: "#6aa3ff"
        anchors.horizontalCenter: track.horizontalCenter
        y: track.y + (1.0 - root.value) * (track.height - height)

        // Smooth movement while dragging (no inertia)
        Behavior on y { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    }

    MouseArea {
        anchors.fill: track
        onPressed: function(mouse) {
            root._pressY = mouse.y
            root._startValue = root.value
        }
        onPositionChanged: function(mouse) {
            if (!pressed) return
            var dy = mouse.y - root._pressY
            var dv = -(dy / track.height) // moving down decreases value
            var v = root._startValue + dv
            root.value = Math.max(0, Math.min(1, v))
        }
    }
}
