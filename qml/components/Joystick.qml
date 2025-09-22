import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property real scaleFactor: 1.0
    // -1..1 normalized output
    property real xValue: 0
    property real yValue: 0
    signal moved(real x, real y)

    implicitWidth: (typeof controller !== 'undefined' && controller) ? controller.scaled(220) : 220
    implicitHeight: implicitWidth

    readonly property real borderWidth: 2
    // Maximize radius to the visible circle edge (centered circle)
    readonly property real radius: Math.max(1, Math.min(width, height) / 2 - borderWidth / 2)
    readonly property real thumbRadius: Math.min(width, height) * 0.18 * 0.5
    readonly property real effectiveRadius: Math.max(1, radius - thumbRadius)
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2

    // Drag state to avoid jump-to-click
    property real _pressX: 0
    property real _pressY: 0
    property real _startXValue: 0
    property real _startYValue: 0

    // Visible base circle (centered)
    Rectangle {
        id: base
        width: root.radius * 2
        height: width
        anchors.centerIn: parent
        radius: width / 2
        color: "#1e1e1e"
        border.color: "#3d3d3d"
        border.width: root.borderWidth
    }

    // Thumb
    Rectangle {
        id: thumb
        width: Math.min(root.width, root.height) * 0.18
        height: width
        radius: width / 2
        color: "#2e6bd1"
        border.color: "#6aa3ff"
        x: root.centerX + root.xValue * root.effectiveRadius - width/2
        y: root.centerY + root.yValue * root.effectiveRadius - height/2

        // Smooth return-to-center animation (no inertia)
        Behavior on x { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        onPressed: function(mouse) {
            // Record starting point and values; do not jump thumb
            root._pressX = mouse.x
            root._pressY = mouse.y
            root._startXValue = root.xValue
            root._startYValue = root.yValue
        }
        onPositionChanged: function(mouse) {
            if (!pressed) return
            var dx = mouse.x - root._pressX
            var dy = mouse.y - root._pressY
            // Convert pixel delta to normalized change
            var nx = root._startXValue + (dx / root.effectiveRadius)
            var ny = root._startYValue + (dy / root.effectiveRadius)
            // Clamp to unit circle (normalize if outside)
            var mag2 = nx*nx + ny*ny
            if (mag2 > 1.0) {
                var mag = Math.sqrt(mag2)
                nx /= mag
                ny /= mag
            }
            root.xValue = nx
            root.yValue = ny
            root.moved(root.xValue, root.yValue)
        }
        onReleased: {
            // Smoothly return to center
            root.xValue = 0
            root.yValue = 0
            root.moved(0, 0)
        }
    }
}
