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

    readonly property real radius: Math.min(width, height) * 0.45
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2

    // Drag state to avoid jump-to-click
    property real _pressX: 0
    property real _pressY: 0
    property real _startXValue: 0
    property real _startYValue: 0

    Rectangle {
        id: base
        anchors.fill: parent
        radius: Math.min(width, height) / 2
        color: "#1e1e1e"
        border.color: "#3d3d3d"
    }

    // Thumb
    Rectangle {
        id: thumb
        width: Math.min(root.width, root.height) * 0.18
        height: width
        radius: width / 2
        color: "#2e6bd1"
        border.color: "#6aa3ff"
        x: root.centerX + root.xValue * root.radius - width/2
        y: root.centerY + root.yValue * root.radius - height/2

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
            var nx = root._startXValue + (dx / root.radius)
            var ny = root._startYValue + (dy / root.radius)
            // Clamp to -1..1
            nx = Math.max(-1, Math.min(1, nx))
            ny = Math.max(-1, Math.min(1, ny))
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
