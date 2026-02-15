import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: root
    property real scaleFactor: 1.0

    // Edit mode state
    property bool editMode: false
    property bool showGrid: true
    property int gridSnap: 10

    // Widget model - loaded from profile via bridge
    property var widgetModel: []

    // Load layout from bridge on creation
    Component.onCompleted: {
        if (controller) {
            var data = controller.getCustomLayout()
            if (data && data.length > 0) {
                widgetModel = JSON.parse(data)
                gridSnap = controller.getCustomLayoutGridSnap()
                showGrid = controller.getCustomLayoutShowGrid()
            }
        }
    }

    // ==================== CANVAS BACKGROUND ====================
    Rectangle {
        id: canvas
        anchors.fill: parent
        anchors.rightMargin: editMode ? 170 : 0
        color: "#111111"
        clip: true

        Behavior on anchors.rightMargin {
            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
        }

        // Grid overlay
        Canvas {
            id: gridCanvas
            anchors.fill: parent
            visible: editMode && showGrid
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "#222222"
                ctx.lineWidth = 0.5

                var step = root.gridSnap > 0 ? root.gridSnap : 10

                // Vertical lines
                for (var x = 0; x <= width; x += step) {
                    ctx.beginPath()
                    ctx.moveTo(x, 0)
                    ctx.lineTo(x, height)
                    ctx.stroke()
                }
                // Horizontal lines
                for (var y = 0; y <= height; y += step) {
                    ctx.beginPath()
                    ctx.moveTo(0, y)
                    ctx.lineTo(width, y)
                    ctx.stroke()
                }
            }
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onVisibleChanged: requestPaint()
        }

        // Edit mode instruction banner
        Rectangle {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 8
            width: editBannerText.width + 30
            height: 28
            radius: 14
            color: "#333"
            border.color: "#4a9eff"
            border.width: 1
            visible: editMode
            z: 200

            Text {
                id: editBannerText
                anchors.centerIn: parent
                text: "Edit Mode — Drag to move, corner to resize, double-click to configure"
                color: "#4a9eff"
                font.pixelSize: 11
                font.bold: true
            }
        }

        // ==================== WIDGET REPEATER ====================
        Repeater {
            id: widgetRepeater
            model: root.widgetModel.length

            Comp.DraggableWidget {
                id: dragWidget

                // Pull data from model
                property var wData: root.widgetModel[index] || {}

                x: wData.x || 0
                y: wData.y || 0
                width: wData.width || 100
                height: wData.height || 100

                widgetId: wData.id || ""
                widgetType: wData.type || "button"
                widgetLabel: wData.label || ""
                buttonId: wData.button_id || 1
                widgetColor: wData.color || "#333"
                widgetShape: wData.shape || "rounded"
                orientation: wData.orientation || "horizontal"
                mapping: wData.mapping || {}
                centerReturn: wData.center_return || false
                toggleMode: wData.toggle_mode || false

                editMode: root.editMode
                gridSnap: root.gridSnap

                onWidgetMoved: function(wid, wx, wy) {
                    _updateWidgetProp(wid, "x", wx)
                    _updateWidgetProp(wid, "y", wy)
                }

                onWidgetResized: function(wid, ww, wh) {
                    _updateWidgetProp(wid, "width", ww)
                    _updateWidgetProp(wid, "height", wh)
                }

                onWidgetRemoved: function(wid) {
                    _removeWidget(wid)
                }

                onWidgetConfigRequested: function(wid) {
                    configDialog.openForWidget(wid)
                }
            }
        }
    }

    // ==================== WIDGET PALETTE (right sidebar in edit mode) ====================
    Comp.WidgetPalette {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 160
        editMode: root.editMode
        widgetModel: root.widgetModel

        onAddWidget: function(widgetData) {
            root._addWidget(widgetData)
        }

        onSaveLayout: {
            root._saveLayout()
        }

        onToggleGrid: {
            root.showGrid = !root.showGrid
            gridCanvas.requestPaint()
        }
    }

    // ==================== EDIT MODE TOGGLE BUTTON ====================
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: root.editMode ? 172 : 12
        anchors.bottomMargin: 12
        width: editToggleRow.width + 20
        height: 36
        radius: 18
        color: root.editMode ? "#4a9eff" : "#333"
        border.color: root.editMode ? "#6ab8ff" : "#555"
        border.width: 1
        z: 300

        Row {
            id: editToggleRow
            anchors.centerIn: parent
            spacing: 6

            Text {
                text: root.editMode ? "✓" : "✏"
                color: "white"
                font.pixelSize: 14
            }
            Text {
                text: root.editMode ? "Done Editing" : "Edit Layout"
                color: "white"
                font.pixelSize: 12
                font.bold: true
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                root.editMode = !root.editMode
                if (!root.editMode) {
                    // Auto-save on exit edit mode
                    root._saveLayout()
                }
            }
        }
    }

    // ==================== WIDGET CONFIG DIALOG ====================
    Rectangle {
        id: configDialog
        anchors.centerIn: parent
        width: 360
        height: configContent.height + 20
        radius: 12
        color: "#2a2a2a"
        border.color: "#4a9eff"
        border.width: 2
        visible: false
        z: 500

        property string targetWidgetId: ""
        property var targetWidget: null

        function openForWidget(wid) {
            for (var i = 0; i < root.widgetModel.length; i++) {
                if (root.widgetModel[i].id === wid) {
                    targetWidgetId = wid
                    targetWidget = root.widgetModel[i]
                    labelField.text = targetWidget.label || ""
                    if (targetWidget.type === "button") {
                        buttonIdField.text = String(targetWidget.button_id || 1)
                        colorField.text = targetWidget.color || "#333"
                        shapeCombo.currentIndex = ["circle", "rounded", "square"].indexOf(targetWidget.shape || "rounded")
                    }
                    if (targetWidget.type === "button") {
                        toggleModeSwitch.checked = targetWidget.toggle_mode || false
                    }
                    if (targetWidget.type === "joystick") {
                        var axPair = (targetWidget.mapping.axis_x || "x") + "/" + (targetWidget.mapping.axis_y || "y")
                        axisPairCombo.currentIndex = ["x/y", "rx/ry", "z/rz", "sl0/sl1"].indexOf(axPair)
                        if (axisPairCombo.currentIndex < 0) axisPairCombo.currentIndex = 0
                    }
                    if (targetWidget.type === "slider" || targetWidget.type === "wheel") {
                        var slAxis = targetWidget.mapping.axis || "z"
                        sliderAxisCombo.currentIndex = ["z", "rz", "sl0", "sl1", "x", "y", "rx", "ry"].indexOf(slAxis)
                        if (sliderAxisCombo.currentIndex < 0) sliderAxisCombo.currentIndex = 0
                        if (targetWidget.type === "slider") {
                            centerReturnSwitch.checked = targetWidget.center_return || false
                        }
                    }
                    visible = true
                    return
                }
            }
        }

        // Dim background
        Rectangle {
            parent: root
            anchors.fill: parent
            color: "#00000088"
            visible: configDialog.visible
            z: 499

            MouseArea {
                anchors.fill: parent
                onClicked: configDialog.visible = false
            }
        }

        Column {
            id: configContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 16
            spacing: 10

            Text {
                text: "Configure Widget"
                color: "#fff"
                font.pixelSize: 16
                font.bold: true
            }

            Rectangle { width: parent.width; height: 1; color: "#444" }

            // Label
            Row {
                spacing: 8
                Text { text: "Label:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                Rectangle {
                    width: 200; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                    TextInput {
                        id: labelField
                        anchors.fill: parent
                        anchors.margins: 6
                        color: "white"
                        font.pixelSize: 12
                    }
                }
            }

            // Button-specific fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? configDialog.targetWidget.type === "button" : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Button ID:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 80; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput {
                            id: buttonIdField
                            anchors.fill: parent
                            anchors.margins: 6
                            color: "white"
                            font.pixelSize: 12
                            validator: IntValidator { bottom: 1; top: 128 }
                        }
                    }
                    Text { text: "(1-128)"; color: "#888"; font.pixelSize: 10; verticalAlignment: Text.AlignVCenter; height: 30 }
                }

                Row {
                    spacing: 8
                    Text { text: "Color:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 120; height: 30; radius: 4; color: "#1a1a1a"; border.color: "#444"
                        TextInput {
                            id: colorField
                            anchors.fill: parent
                            anchors.margins: 6
                            color: "white"
                            font.pixelSize: 12
                        }
                    }
                    Rectangle {
                        width: 30; height: 30; radius: 4
                        color: colorField.text || "#333"
                        border.color: "#666"
                        border.width: 1
                    }
                }

                Row {
                    spacing: 8
                    Text { text: "Shape:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: shapeCombo
                        width: 120
                        model: ["circle", "rounded", "square"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: shapeCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                    }
                }

                // Toggle mode
                Row {
                    spacing: 8
                    Text { text: "Mode:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 180; height: 30; radius: 4; color: "transparent"
                        Row {
                            spacing: 8
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                id: toggleModeSwitch
                                property bool checked: false
                                width: 44; height: 22; radius: 11
                                color: checked ? "#16a34a" : "#555"
                                Rectangle {
                                    width: 18; height: 18; radius: 9
                                    color: "white"
                                    x: parent.checked ? parent.width - width - 2 : 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 120 } }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: parent.checked = !parent.checked
                                }
                            }
                            Text {
                                text: toggleModeSwitch.checked ? "Toggle" : "Momentary"
                                color: toggleModeSwitch.checked ? "#4ade80" : "#aaa"
                                font.pixelSize: 11
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }

            // Joystick-specific fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? configDialog.targetWidget.type === "joystick" : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Axis Pair:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: axisPairCombo
                        width: 200
                        model: ["x/y (Left Stick)", "rx/ry (Right Stick)", "z/rz (Throttle/Rudder)", "sl0/sl1 (Slider Axes)"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: axisPairCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }

            // Slider & Wheel axis fields
            Column {
                spacing: 8
                visible: configDialog.targetWidget ? (configDialog.targetWidget.type === "slider" || configDialog.targetWidget.type === "wheel") : false
                width: parent.width

                Row {
                    spacing: 8
                    Text { text: "Axis:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Basic.ComboBox {
                        id: sliderAxisCombo
                        width: 200
                        model: ["z (LT/Throttle)", "rz (RT/Rudder)", "sl0 (Slider 0)", "sl1 (Slider 1)", "x", "y", "rx", "ry"]
                        background: Rectangle { color: "#1a1a1a"; border.color: "#444"; radius: 4 }
                        contentItem: Text { text: sliderAxisCombo.displayText; color: "white"; font.pixelSize: 12; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                    }
                }

                // Center return (slider only)
                Row {
                    spacing: 8
                    visible: configDialog.targetWidget ? configDialog.targetWidget.type === "slider" : false
                    Text { text: "Center:"; color: "#ccc"; font.pixelSize: 12; width: 70; verticalAlignment: Text.AlignVCenter; height: 30 }
                    Rectangle {
                        width: 200; height: 30; radius: 4; color: "transparent"
                        Row {
                            spacing: 8
                            anchors.verticalCenter: parent.verticalCenter
                            Rectangle {
                                id: centerReturnSwitch
                                property bool checked: false
                                width: 44; height: 22; radius: 11
                                color: checked ? "#2e6bd1" : "#555"
                                Rectangle {
                                    width: 18; height: 18; radius: 9
                                    color: "white"
                                    x: parent.checked ? parent.width - width - 2 : 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 120 } }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: parent.checked = !parent.checked
                                }
                            }
                            Text {
                                text: centerReturnSwitch.checked ? "Spring to center" : "Hold position"
                                color: centerReturnSwitch.checked ? "#6aa3ff" : "#aaa"
                                font.pixelSize: 11
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }

            Rectangle { width: parent.width; height: 1; color: "#444" }

            // Dialog buttons
            Row {
                spacing: 10
                anchors.right: parent.right

                Rectangle {
                    width: 70; height: 32; radius: 6
                    color: cancelConfigArea.containsMouse ? "#444" : "#333"
                    border.color: "#555"
                    Text { anchors.centerIn: parent; text: "Cancel"; color: "#ccc"; font.pixelSize: 12 }
                    MouseArea { id: cancelConfigArea; anchors.fill: parent; hoverEnabled: true; onClicked: configDialog.visible = false }
                }

                Rectangle {
                    width: 70; height: 32; radius: 6
                    color: applyConfigArea.containsMouse ? "#1a8cff" : "#0078d4"
                    Text { anchors.centerIn: parent; text: "Apply"; color: "white"; font.pixelSize: 12; font.bold: true }
                    MouseArea {
                        id: applyConfigArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            var wid = configDialog.targetWidgetId
                            _updateWidgetProp(wid, "label", labelField.text)

                            if (configDialog.targetWidget.type === "button") {
                                _updateWidgetProp(wid, "button_id", parseInt(buttonIdField.text) || 1)
                                _updateWidgetProp(wid, "color", colorField.text)
                                _updateWidgetProp(wid, "shape", shapeCombo.currentText)
                                _updateWidgetProp(wid, "toggle_mode", toggleModeSwitch.checked)
                            }

                            if (configDialog.targetWidget.type === "joystick") {
                                var axisPairs = [["x", "y"], ["rx", "ry"], ["z", "rz"], ["sl0", "sl1"]]
                                var pair = axisPairs[axisPairCombo.currentIndex] || ["x", "y"]
                                _updateWidgetProp(wid, "mapping", {"axis_x": pair[0], "axis_y": pair[1]})
                            }

                            if (configDialog.targetWidget.type === "slider" || configDialog.targetWidget.type === "wheel") {
                                var sliderAxes = ["z", "rz", "sl0", "sl1", "x", "y", "rx", "ry"]
                                _updateWidgetProp(wid, "mapping", {"axis": sliderAxes[sliderAxisCombo.currentIndex] || "z"})
                                if (configDialog.targetWidget.type === "slider") {
                                    _updateWidgetProp(wid, "center_return", centerReturnSwitch.checked)
                                }
                            }

                            configDialog.visible = false
                            // Force model refresh
                            var tmp = root.widgetModel
                            root.widgetModel = []
                            root.widgetModel = tmp
                        }
                    }
                }
            }
        }
    }

    // ==================== HELPER FUNCTIONS ====================
    function _updateWidgetProp(wid, prop, value) {
        for (var i = 0; i < widgetModel.length; i++) {
            if (widgetModel[i].id === wid) {
                widgetModel[i][prop] = value
                return
            }
        }
    }

    function _addWidget(data) {
        var m = widgetModel.slice()
        m.push(data)
        widgetModel = m
    }

    function _removeWidget(wid) {
        var m = []
        for (var i = 0; i < widgetModel.length; i++) {
            if (widgetModel[i].id !== wid) {
                m.push(widgetModel[i])
            }
        }
        widgetModel = m
    }

    function _saveLayout() {
        if (controller) {
            controller.saveCustomLayout(JSON.stringify(widgetModel), gridSnap, showGrid)
        }
    }
}
